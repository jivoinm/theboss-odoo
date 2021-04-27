# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _inherit = "project.task"

    mrp_production_id = fields.Many2one(
        'mrp.production',
        string='Mrp Production')
    visible_production = fields.Boolean('Display production', compute='_compute_visible_production', readonly=True)
    production_state = fields.Char('Production status', compute='_compute_production_state', readonly=True)    

    @api.depends('mrp_production_id.state')
    def _compute_production_state(self):
        for task in self:
            if task.mrp_production_id:
                task.production_state = dict(self.env['mrp.production'].fields_get(allfields=['state'])['state']['selection'])[task.mrp_production_id.state]
                task.stage_id = self.get_or_create('project.task.type', task.production_state, {'name': task.production_state})
                if task.mrp_production_id.state == 'done':
                    task.date_end = task.mrp_production_id.date_finished
            else:
                task.production_state = 'Not created'
    @api.depends('mrp_production_id')
    def _compute_visible_production(self):
        for task in self:
            task.visible_production = task.mrp_production_id.id == True

    def get_or_create(self, entity, name, create_object=False):
        to_create = self.env[entity].search([('name', '=', name)], limit=1)
        if not to_create :
            to_create = self.env[entity].create(create_object if create_object else {'name': name})
        return to_create

    def get_or_create_product(self, name, warehouse):
        return self.get_or_create('product.product', name, {
                'name': name,
                'type': 'product',
                'uom_id': self.env.ref("uom.product_uom_unit").id,
                'uom_po_id': self.env.ref("uom.product_uom_unit").id,
                'service_tracking': 'no',
                'project_id': False,
                'taxes_id': False,
                'sale_ok': False,
                'purchase_ok': False,
                'categ_id': self.env.ref('product.product_category_all').id,
                'route_ids': [(4, self.env.ref('mrp.route_warehouse0_manufacture').id)]
                })

    def create_product(self, name, warehouse):
        product_to_build = self.get_or_create_product(name, warehouse)
        component_1 = self.get_or_create('product.product', 'Component To Order', {
            'name': 'Component To Order',
            'project_id': False,
            'sale_ok': False,
            'purchase_ok': True,
        })
        wc_1 = self.get_or_create('mrp.workcenter', 'Work Center 1')
        wc_2 = self.get_or_create('mrp.workcenter', 'Work Center 2')
        wc_3 = self.get_or_create('mrp.workcenter', 'Work Center 3')
        wc_4 = self.get_or_create('mrp.workcenter', 'Work Center 4')
        
        bom_1 = self.env['mrp.bom'].create({
            'product_id': product_to_build.id,
            'product_tmpl_id': product_to_build.product_tmpl_id.id,
            'product_uom_id': product_to_build.uom_id.id,
            'product_qty': 1.00,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': component_1.id, 'product_qty': 1.00})
            ],
            'operation_ids': [
                (0, 0, {'sequence': 1, 'name': 'Parts and Doors', 'workcenter_id': wc_1.id}),
                (0, 0, {'sequence': 2, 'name': 'Cutting', 'workcenter_id': wc_2.id}),
                (0, 0, {'sequence': 2, 'name': 'Finishing', 'workcenter_id': wc_3.id}),
                (0, 0, {'sequence': 2, 'name': 'Assembly', 'workcenter_id': wc_4.id}),
            ]})
        return product_to_build, bom_1

    def validateIfMrpCanBeCreated(self, project_task):
        if not project_task.date_deadline:
            self.show_error_message("You need to set the Project Task Deadline before creating Manufactoring Order!")
            return False
        return True

    def show_error_message(self, message):
        raise UserError(_(message))

    def _setMOValues(self, mo):
        for project_task in self:
            mo.sale_order_id = project_task.sale_line_id.order_id.id
            mo.partner_id = project_task.sale_line_id.order_id.partner_id
            mo.origin = project_task.sale_line_id.order_id.name

    def action_create_mrp_production(self):
        self.ensure_one()
        action = {}
        for project_task in self:
            if self.validateIfMrpCanBeCreated(project_task):
                if project_task.sale_line_id and not project_task.mrp_production_id:
                    company = self.env['res.company']._company_default_get('project.task')
                    warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
                    product_to_build, bom = self.create_product("[{0}] - [{1}]".format(project_task.sale_line_id.product_id.name, project_task.sale_line_id.order_id.name), warehouse)
                    if product_to_build:
                        picking_customer = self.env['stock.picking'].create({
                            'location_id': warehouse.wh_output_stock_loc_id.id,
                            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                            'partner_id': project_task.sale_line_id.order_id.partner_id.id,
                            'picking_type_id': warehouse.out_type_id.id,

                        })
                        move_to_customer = self.env['stock.move'].create({
                            'name': 'WO/MO/{0}'.format(product_to_build.name),
                            'product_id': product_to_build.id,
                            'product_uom': self.env.ref('uom.product_uom_unit').id,
                            'picking_id': picking_customer.id,
                            'date': project_task.date_deadline,
                            'date_deadline': project_task.date_deadline,
                            'location_id': self.env.ref('stock.stock_location_stock').id,
                            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                            'product_uom_qty': project_task.sale_line_id.product_uom_qty,
                            'procure_method': 'make_to_order'
                        })

                        move_to_customer._action_confirm()
                        mo = self.env['mrp.production'].search([
                            ('product_id', '=', product_to_build.id),
                            ('state', '=', 'confirmed')
                        ], limit=1)
                        self._setMOValues(mo)
                        project_task.mrp_production_id = mo.id
                action = {
                    'res_model': 'mrp.production',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_id': project_task.mrp_production_id.id,
                    }
        return action

    @api.onchange('stage_id')
    def check_if_tasks_are_done(self):
        self.ensure_one()
        action = {}
        for project_task in self:
            undone_tasks = self.env['mail.activity'].search([('res_model', '=', 'project.task'), ('res_id', '=',  project_task._origin.id)])
            if undone_tasks:
               self.show_error_message("There are some unfinished tasks!")
               project_task.stage_id.id = project_task._origin.stage_id.id
        return action