# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, _
import logging
import wdb

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    order_details = fields.Char(string='Order Details')
    customer_details = fields.Char(string='Customer Details', readonly=True, compute='_compute_customer_details')
    document_ids = fields.One2many('ir.attachment', compute='_compute_document_ids', string="Job Files", help="Job files linked to this Production WO")
    documents_count = fields.Integer(compute='_compute_document_ids', string="Document Count")

    def _compute_document_ids(self):
        attachments = self.env['ir.attachment'].search([('res_id', '=', self.sale_order_id.id), ('res_model', '=', 'sale.order')])
        result = dict.fromkeys(attachments.ids, self.env['ir.attachment'])
        for attachment in attachments:
            result[attachment.res_id] = attachment

        for mrp in self:
            mrp.document_ids = result.get(self.sale_order_id.id, False)
            mrp.documents_count = len(mrp.document_ids)

    @api.depends('partner_id')
    def _compute_customer_details(self):
        for record in self:
            record.customer_details = record.partner_id._display_address()

    def attachment_tree_view(self):
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        action['domain'] = str([
            '&',
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.sale_order_id.id)
        ])
        action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % ('sale.order', self.sale_order_id.id)
        return action