# -*- coding: utf-8 -*-

from odoo import models, fields, api
#from openerp.addons.base_geoengine import geo_model
#from openerp.addons.base_geoengine import fields as geo_fields


#class agro_property(geo_model.GeoModel):
class agro_activity_task(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'

class agro_property(models.Model):
    _name = 'agro.property'

    name = fields.Char(required=True)
    description = fields.Text()
    property_type_id = fields.Many2one('agro.property.type', 'Property Type', required=True)
#    the_geom = geo_fields.GeoMultiPolygon('Property Shape')

class agro_property_type(models.Model):
    _name = 'agro.property.type'

    name = fields.Char(required=True)
    is_cultivable = fields.Boolean()

class culture(models.Model):
    _name = 'agro.culture'

    name = fields.Char(required=True)
    description = fields.Text()
    code = fields.Char()
    recepie_ids = fields.Many2many('agro.culture.recepie',
                            'agro_culture_recepie_rel',
                            'culture_id',
                            'culture_recepie_id',
                            string='Recepies', required=True)

class culture_recepie(models.Model):
    _name = 'agro.culture.recepie'

    name = fields.Char(required=True)
    description = fields.Char()
    create_po = fields.Boolean(string='Create Purchase Order')
    create_wo = fields.Boolean(string='Create Work Order')

class campaign(models.Model):
    _name = 'agro.campaign'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(required=True)
    description = fields.Text()
    year = fields.Integer(help='Year for this campain', required=True)
    duration = fields.Integer(help='Number of months campain should take')
    culture_id = fields.Many2one('agro.culture', 'Culture type', required=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('progress', 'In progress'),
            ('finished', 'Done'),
            ],default='draft')

    property_ids = fields.Many2many('agro.property',
                            'agro_campaign_property_rel',
                            'campaign_id',
                            'agro_property_id',
                            string="Properties", required=True)
    tasks = fields.Integer(compute='related_tasks')

    def related_tasks(self):
        #self.tasks = self.env['project.project'].search_count([('alias_id', '=', self.id), ('alias_model', '=', 'agro.campaign')])
        self.tasks = 0


    #This function is triggered when the user clicks on the button 'Approved'
    @api.one
    def approve_button(self):
        for prop in self.property_ids:
            for recepie in self.culture_id.recepie_ids:
                if recepie.create_wo == True:
                    self.env['project.task'].create({'name': prop.name + ' - ' + recepie.name + ' WO'})

        self.env.cr.commit()
        self.write({
    	   'state': 'approved',
           'description': 'Approved this campaign'
        })
