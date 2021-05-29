# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.user.sale_team_id:
                vals['team_id'] = self.env.user.sale_team_id.id
        partners = super(ResPartner, self).create(vals_list)
        return partners


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain=lambda self: ['&', ('team_id', '=', self.env.user.sale_team_id.id if self.env.user.sale_team_id else False), ('customer_rank', '=', 1)])

    doors = fields.Selection(
        string='Doors',
        selection=[('na', 'N/A'), ('all_ordered', 'All Ordererd'), ('all_made_in_shop', 'All Made In Shop'), ('some_made_in_shop', 'Some Made In Shop')]
    )

    door_vendor_id = fields.Many2one('res.partner', string='Doors Vendor', required=False,
        change_default=True, tracking=True,
        help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    nr_of_counter_tops = fields.Integer(
        string='Nr Of Counter Tops'
    )

    nr_of_glass_pieces = fields.Integer(
        string='Nr Of Glass Pieces'
    )
    
    attachment_number = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    
    commitment_date = fields.Date('Delivery Date', copy=False,
                                    states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                    help="This is the delivery date promised to the customer. "
                                        "If set, the delivery order will be scheduled based on "
                                        "this date rather than product lead times.")

    def _get_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'hr.applicant'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = dict((res['res_id'], res['res_id_count']) for res in read_group_res)
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)

    def _action_confirm(self):
        """ On SO confirmation, some lines should generate a task or a project. """
        result = super()._action_confirm()

    @api.depends('order_line.product_id.service_tracking')
    def _compute_visible_project(self):
        """ Users should be able to select a project_id on the SO if at least one SO line has a product with its service tracking
        configured as 'task_in_project' """
        for order in self:
            order.visible_project = any(
                service_tracking == 'task_in_project' for service_tracking in order.order_line.mapped('product_id.service_tracking')
            )
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    upper_door_style_colour = fields.Char(
        string='Style & Colour',
        help='Upper Door Style & Colour',
    )

    door_hardware = fields.Char(
        string='Door Hdw.',
        help='Door Hardware',
    )

    drawer_hardware = fields.Char(
        string='Drawer Hadw.',
        help='Drawer Hardware',
    )

    cabinet_colour = fields.Char(
        string='Cab. Colour',
        help='Cabinet Colour',
    )

    counter_top_style = fields.Char(
        string='C.Top Style',
        help='Counter Top Style',
    )

    counter_top_colour = fields.Char(
        string='C.Top Colour',
        help='Counter Top Colour',
    )

    counter_top_code = fields.Char(
        string='C.Top Code',
        help='Counter Top Code',
    )
    
    def xstr(self, s):
        if s == False:
            return ''
        return str(s)
    def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        #wdb.set_trace()
        planned_hours = self._convert_qty_company_hours(self.company_id)
        sale_line_name_parts = self.name.split('\n')
        title = sale_line_name_parts[0] or self.product_id.name
        description = '<br/>'.join(sale_line_name_parts[1:])
        description = '%s <br/> Style & Colour: %s<br/> Door Hardware: %s<br/> Drawer Hardware: %s<br/> Cabinet Colour: %s<br/> Counter Top Style: %s<br/> Counter Top Colour: %s<br/> Counter Top Code: %s' % (description, self.xstr(self.upper_door_style_colour), self.xstr(self.door_hardware), self.xstr(self.drawer_hardware), self.xstr(self.cabinet_colour), self.xstr(self.counter_top_style), self.xstr(self.counter_top_colour), self.xstr(self.counter_top_code))
        
        return {
            'name': title if project.sale_line_id else '%s: %s' % (self.order_id.name or '', title),
            'planned_hours': planned_hours,
            'partner_id': self.order_id.partner_id.id,
            'email_from': self.order_id.partner_id.email,
            'description': description,
            'project_id': project.id,
            'sale_line_id': self.id,
            'date_deadline': self.order_id.commitment_date,
            'sale_order_id': self.order_id.id, 
            'company_id': project.company_id.id,
            'user_id': False,  # force non assigned task, as created as sudo()
        }
