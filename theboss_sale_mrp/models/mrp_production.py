# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Integer(
        "Sale Order",
        compute='_compute_sale_order')


    @api.depends('move_dest_ids.sale_line_id.order_id')
    def _compute_sale_order(self):
        for record in self:
            record.sale_order_id = record.move_dest_ids.sale_line_id.order_id

    def action_view_sale_order(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.sale_order_id,
            }
        return action

class StockRule(models.Model):

    _inherit = ['stock.rule']
    @api.model
    def _run_manufacture(self, procurements):
        for procurement, rule in procurements:
            _logger.info("StockRule... procurement {0}".format(procurement))

