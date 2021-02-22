# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import wdb

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    doors = fields.Selection(
        string='Doors',
        selection=[('na', 'N/A'), ('all_ordered', 'All Ordererd'), ('all_made_in_shop', 'All Made In Shop'), ('some_made_in_shop', 'Some Made In Shop')]
    )

    door_vendor_id = fields.Many2one('res.partner', string='Doors Vendor', required=True,
        change_default=True, tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    nr_of_counter_tops = fields.Integer(
        string='Nr Of Counter Tops'
    )

    nr_of_glass_pieces = fields.Integer(
        string='Nr Of Glass Pieces'
    )

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
        string='Upper Door Style & Colour',
    )

    door_hardware = fields.Char(
        string='Door Hardware',
    )

    drawer_hardware = fields.Char(
        string='Drawer Hardware',
    )

    cabinet_colour = fields.Char(
        string='Cabinet Colour',
    )

    counter_top_style = fields.Char(
        string='Counter Top Style',
    )

    counter_top_colour = fields.Char(
        string='Counter Top Colour',
    )

    counter_top_code = fields.Char(
        string='Counter Top Code',
    )

