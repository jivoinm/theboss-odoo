# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class res_company_caen(models.Model):
    _name = "res.company.caen"
    _description = "CAEN codes for Romanian Companies"

    code = fields.Char('CAEN code', required=True, help='CAEN code')
    name = fields.Char('CAEN name', required=True, help='CAEN name')
    trisc = fields.Float('Accident Coefficient', required=True, digits=(0,4))


class res_company(models.Model):
    _inherit = "res.company"

    codcaen = fields.Many2one(
        'res.company.caen', 'CAEN code', help="Company CAEN code.")
    coefacc = fields.Float(
        string='Accident Coefficient', related='codcaen.trisc', digits=(0,4))