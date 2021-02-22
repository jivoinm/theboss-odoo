# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import wdb

class ProjectTask(models.Model):
    _inherit = "project.task"

    mrp_production_id = fields.Many2one(
        'mrp.production',
        string='Mrp Production')
   
    def get_or_create_product(self, name, warehouse):
        product = self.env['product.product'].search([('name', '=', name)], limit=1)
        if not product:
            route_manufacture = warehouse.manufacture_pull_id.route_id.id
            route_mto = warehouse.mto_pull_id.route_id.id
            product = self.env['product.product'].create({
                'name': name,
                'type': 'product',
                'uom_id': self.env.ref("uom.product_uom_unit").id,
                'uom_po_id': self.env.ref("uom.product_uom_unit").id,
                'service_tracking': 'no',
                'project_id': False,
                'taxes_id': False,
                'categ_id': self.env.ref('product.product_category_all').id,
                'route_ids': [(6, 0, [route_manufacture, route_mto])]
                })
        return product
    def create_product(self, name, warehouse):
        product_to_build = self.get_or_create_product(name, warehouse)
        product_to_use_1 = self.get_or_create_product('Component To Order', warehouse)
        bom_1 = self.env['mrp.bom'].create({
            'product_id': product_to_build.id,
            'product_tmpl_id': product_to_build.product_tmpl_id.id,
            'product_uom_id': product_to_build.uom_id.id,
            'product_qty': 1.00,
            'type': 'normal',
            'consumption': 'flexible',
            'bom_line_ids': [
                (0, 0, {'product_id': product_to_use_1.id, 'product_qty': 1.00})
            ]})
        return product_to_build, bom_1

    def show_warning_message(self, message):
         return {
                    "warning": {"title": _("Warning"), "message": _(message)},
                } 

    def action_create_mrp_production(self):
        self.ensure_one()
        wdb.set_trace()
        for project_task in self:
            if not project_task.date_deadline:
                return self.show_warning_message("You need to set the Project Task Deadline before creating Manufactoring Order!")
            if project_task.sale_line_id and not project_task.mrp_production_id:
                company = self.env['res.company']._company_default_get('project.task')
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
                product_to_build, bom = self.create_product("[{0}] - [{1}]".format(project_task.sale_line_id.product_id.name, project_task.sale_line_id.order_id.name), warehouse)
                if product_to_build:
                    mrp_production = self.env["mrp.production"].create({
                                            'sale_order_id': project_task.sale_line_id.order_id.id,
                                            'product_id': product_to_build.id,
                                            'bom_id': bom.id,
                                            'product_uom_qty': project_task.sale_line_id.product_uom_qty,
                                            'product_qty': project_task.sale_line_id.product_uom_qty,
                                            'qty_producing': project_task.sale_line_id.product_uom_qty,
                                            'product_uom_id': project_task.sale_line_id.product_uom.id,
                                            'origin': project_task.name,
                                            'date_planned_start': project_task.date_deadline,
                                            'picking_type_id': warehouse.manu_type_id,
                                            'move_raw_ids': bom.bom_line_ids
                                            })
                    
                    project_task.mrp_production_id = mrp_production
                    
                    stock_location = self.env.ref('stock.stock_location_stock')
                    customer_location = self.env.ref('stock.stock_location_customers')
                    move1 = self.env['stock.move'].create({
                        'name': product_to_build.name,
                        'location_id': stock_location.id,
                        'location_dest_id': customer_location.id,
                        'product_id': project_task.sale_line_id.product_id.id,
                        'product_uom': project_task.sale_line_id.product_uom.id,
                        'product_uom_qty': project_task.sale_line_id.product_uom_qty,
                    })
                    move1._action_confirm()
                    move1._action_assign()
            action = {
                'res_model': 'mrp.production',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': project_task.mrp_production_id.id,
                }
        return action

    # @api.multi
    # def action_generate_documents(self):
    #     self.ensure_one()
    #     attachment_ids = self.env['hr.document'].generate_document_attachements(self, 'hr.applicant')
    #     self.write({'attachment_ids': [(2, 0, attachment_ids)]})
    #     return True

    # def generate_document_attachements(self, model, model_name, file_name_query=None):
    #     attachment_ids = []
    #     search_document = [('model', '=', model_name)]
    #     if file_name_query:
    #         search_document.append(file_name_query)
    #     applicant_docs = self.env['hr.document'].search(search_document)
    #     for doc in applicant_docs:
    #         values = doc.get_template(model.id)
    #         report_obj = self.env['ir.actions.report']
            
    #         IrConfig = self.env['ir.config_parameter'].sudo()
    #         base_url = IrConfig.get_param('report.url') or IrConfig.get_param('web.base.url')
    #         html = values['body_html']
    #         layout = self.env['ir.ui.view'].browse(self.env['ir.ui.view'].get_view_id('theboss_hr_document.minimal_layout_hr_doc'))
    #         #layout = self.env['ir.ui.view'].browse(self.env['ir.ui.view'].get_view_id('web.external_layout'))
    #         body = layout.render(dict(subst=True, body=html, base_url=base_url))
    #         #print(body)
    #         pdf_content = report_obj._run_wkhtmltopdf(
    #             [body],
    #         )
            
    #         result = base64.b64encode(pdf_content)
    #         Attachment = self.env['ir.attachment'] 
    #         if Attachment.search_count([('res_id','=', model.id), ('name','=', doc.name), ('res_model', '=', model_name)]) == 0:
    #             file_name = doc.name
    #             attachment_data = {
    #                 'name': file_name,
    #                 'datas_fname': file_name + '.pdf',
    #                 'datas': result,
    #                 'type': 'binary',
    #                 'res_model': model_name,
    #                 'res_id': model.id,
    #             }
    #             attachment_ids.append(Attachment.create(attachment_data).id)
    #     return attachment_ids

    @api.onchange('stage_id')
    def check_if_tasks_are_done(self):
        self.ensure_one()
        #wdb.set_trace()
        for project_task in self:
            undone_tasks = self.env['mail.activity'].search([('res_id', '=', project_task.id)])
            if undone_tasks:
               return self.show_warning_message("There are some unfinished tasks!")
        return {}