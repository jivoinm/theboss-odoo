# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


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

    # mrp_production_status = fields.Char(
    #     string='Mrp Production Status',
    #     compute='_compute_field_production_status'
    # )

    # @api.depends('state')
    # def _compute_field_production_status(self):
    #     for record in self:
    #         if record.state == "sale":
    #             mrp_production = record.env['mrp.production'].search([('sale_order_id','=',record.id)], limit=1)
    #             if mrp_production:
    #                 record.mrp_production_status = mrp_production[0].state
    #         else:
    #             record.mrp_production_status = "N/A"


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
