# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, _
import logging

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    partner_id = fields.Many2one('res.partner', related='sale_order_id.partner_id', string="Cusromer")

class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values, bom):
        _logger.info("Entering _prepare_mo_vals, {0}, origin:{1}, values:{2}, company_id:{3}".format(self, origin,values, company_id))
        vals = super(StockRule, self)._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name, origin, company_id, values, bom)
        if "orderpoint_id" in values:
            _logger.info("orderpoint_id={0}, group_id:{1}".format(values["orderpoint_id"].id, values["orderpoint_id"].group_id.id))
            sales = self.env['sale.order'].search([('id', '=', values["orderpoint_id"].group_id.sale_order_id)])
            _logger.info("found sale order {0}".format(sales.id))
            if len(sales) > 1:
                    raise exceptions.ValidationError(_('More than 1 sale order found for this group'))
            vals['sale_order_id'] = sales.id
        return vals
