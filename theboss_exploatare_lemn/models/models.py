# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class CostProductie(models.Model):
    """ Cost de productie
    """
    _name = 'theboss.cost.productie'
    _order = 'date DESC'

    name = fields.Char(
        string=u'Denumire',
        required=True
    )

    date = fields.Date(
        string=u'Data',
        default=fields.Date.context_today,
    )

    total_metri_cubi = fields.Float(
        string=u'Total metri cubi',
    )

    total = fields.Float(
        string=u'Total',
    )
    
    exploatare_id = fields.Many2one(
        string=u'Exploatare',
        comodel_name='theboss.exploatare',
        ondelete='set null',
    )
    
    
class CostMotorina(models.Model):
    """ Cost de motorina
    """
    _name = 'theboss.cost.motorina'
    _order = 'date DESC'

    name = fields.Char(
        string=u'Denumire',
        required=True
    )

    date = fields.Date(
        string=u'Data',
        default=fields.Date.context_today,
    )

    total_litri = fields.Float(
        string=u'Total litri',
    )

    pret_litru = fields.Float(
        string=u'Pret litru',
    )

    total = fields.Float(
        string=u'Total',
        compute='_compute_total'
    )

    @api.depends('total_litri','pret_litru')
    def _compute_total(self):
        for record in self:
            record.total = record.total_litri * record.pret_litru

    exploatare_id = fields.Many2one(
        string=u'Exploatare',
        comodel_name='theboss.exploatare',
        ondelete='set null',
    )

class Exploatare(models.Model):
    """ Exploatare lemn
    """

    _name = 'theboss.exploatare'
    
    _order = 'date DESC'

    name = fields.Char(
        string=u'Partida',
        required=True
    )

    responsabil_uid = fields.Many2one(
        string=u'Responsabil',
        comodel_name='res.users'
    )

    date = fields.Date(
        string=u'Data productie',
        default=fields.Date.context_today,
    )
    
    cost_metru_cub = fields.Float(
        string=u'Cost metru cub',
        compute='_compute_cost_metru_cub'
    )

    cost_pe_litru = fields.Float(
        string=u'Cost pe litru',
        compute='_compute_cost_pe_litru'
    )

    @api.depends('total_metri_cubi_productie', 'total_litri_motorina')
    def _compute_cost_metru_cub(self):
        for record in self:
            record.cost_metru_cub = (record.total_metri_cubi_productie / record.total_litri_motorina) if record.total_litri_motorina > 0 else 0

    @api.depends('total_metri_cubi_productie', 'total_litri_motorina')
    def _compute_cost_pe_litru(self):
        for record in self:
            record.cost_pe_litru = (record.total_litri_motorina / record.total_metri_cubi_productie) if record.total_metri_cubi_productie > 0 else 0
    
    company_id = fields.Many2one(
        string=u'Licitat de la', 
        comodel_name='res.company', 
    )
    
    detalii = fields.Text(
        string=u'Detalii',
    )
    
    cost_productie_ids = fields.One2many(
        string=u'Costuri Productie',
        comodel_name='theboss.cost.productie',
        inverse_name="exploatare_id",
    )

    cost_motorina_ids = fields.One2many(
        string=u'Costuri Motorina',
        comodel_name='theboss.cost.motorina',
        inverse_name="exploatare_id",
    )
    
    total_cost_productie = fields.Float(
        string=u'Total productie',
        compute='_compute_total_cost_productie'
    )

    @api.depends('cost_productie_ids')
    def _compute_total_cost_productie(self):
        for record in self:
            record.total_cost_productie = sum(cost.total for cost in record.cost_productie_ids)

    total_metri_cubi_productie = fields.Float(
        string=u'Total m3 productie',
        compute='_compute_total_metri_cubi_productie'
    )

    @api.depends('cost_productie_ids')
    def _compute_total_metri_cubi_productie(self):
        for record in self:
            record.total_metri_cubi_productie = sum(cost.total_metri_cubi for cost in record.cost_productie_ids)

    total_cost_motorina = fields.Float(
        string=u'Total motorina',
        compute='_compute_total_cost_motorina'
    )

    @api.depends('cost_motorina_ids')
    def _compute_total_cost_motorina(self):
        for record in self:
            record.total_cost_motorina = sum(cost.total for cost in record.cost_motorina_ids)

    total_litri_motorina = fields.Float(
        string=u'Total litri motorina',
        compute='_compute_total_litri_motorina'
    )

    @api.depends('cost_motorina_ids')
    def _compute_total_litri_motorina(self):
        for record in self:
            record.total_litri_motorina = sum(cost.total_litri for cost in record.cost_motorina_ids)
        