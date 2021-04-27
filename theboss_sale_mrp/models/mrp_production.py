# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, _
import logging

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    partner_id = fields.Many2one('res.partner', related='sale_order_id.partner_id', string="Customer")

    @api.depends(
        'move_raw_ids.state', 'move_raw_ids.quantity_done', 'move_finished_ids.state',
        'workorder_ids', 'workorder_ids.state', 'product_qty', 'qty_producing')
    def _compute_state(self):
        super(MrpProduction, self)._compute_state()
        for mrp in self:
            if mrp.sale_order_id:
                state = dict(self.env['mrp.production'].fields_get(allfields=['state'])['state']['selection'])[mrp.state]
                mrp.sale_order_id.sudo().message_post(
                        body="Manufactoring order %s is in '%s' status and has (%d) work orders done" % (mrp.name, state, mrp.workorder_done_count),
                        author_id=self.env.user.partner_id.id,
                    )
