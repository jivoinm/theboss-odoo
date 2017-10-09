# -*- coding: utf-8 -*-
import logging, datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class fleet_vehicle(models.Model):
    _name = 'fleet.vehicle' # optional
    _inherit = 'fleet.vehicle'

    cm = fields.Float('Consum mediu')
    spor_tractare_remorca1 = fields.Integer(string='Spor remorca 1', help='Sporul specific de tractare, remorca 1')
    spor_tractare_remorca2 = fields.Integer(string='Spor remorca 2', help='Sporul specific de tractare, remorca 2')
    spor_buc = fields.Integer('Spor Bucuresti')
    spor_buc_cu_remorca = fields.Integer('Spor Bucuresti cu remorca')
    spor_judet = fields.Integer('Spor municipii/judet')
    spor_judet_cu_remorca = fields.Integer('Spor municipii/judet cu remorca')
    spor_alte = fields.Integer('Spor celalte orase')
    spor_alte_cu_remorca = fields.Integer('Spor celalte orase cu remorca')
    status = fields.Boolean('Status', compute="_compute_status")
    tank_capacity = fields.Integer()
    external_carid = fields.Integer()
    sarcina_utila_nominala = fields.Float('Sarcina utila nominala (tone)')
    def _compute_status(self):
        return 'm'

class categorie_drum(models.Model):
    _name = 'fleet_fpz.categorie_drum'

    name = fields.Char(string="Categoria de drum Simbolul", required=True)
    coeficient = fields.Char(string="Coeficientul", required=True)
    valoare = fields.Float(string="Valoare", required=True)
    descriere = fields.Text(string="Descriere")

class parcurs_drum(models.Model):
    _name = 'fleet_fpz.parcurs_drum'

    name = fields.Char(compute="_calculate_total_km")
    km = fields.Integer(string="Km", required=True)
    incarcat = fields.Boolean(string="incarcat")
    categorie_drum_id = fields.Many2one(
        string="Cat. drum",
        comodel_name="fleet_fpz.categorie_drum",
        required=True
    )
    km_echivalent = fields.Float('Km echiv.', compute='_calculate_total_km', store=True)
    foaie_de_parcurs_id = fields.Many2one('fleet_fpz.foaie_de_parcurs', 'Foaie de parcurs')

    @api.depends('categorie_drum_id','km')
    def _calculate_total_km(self):
        for record in self:
            if record.categorie_drum_id and record.km:
                #Pe = Ped + T + U + I +/- Ra [km echivalenti]
                #Ped = Suma de la i=1 pina la 6 Pi x Di [km echivalenti]
                #    Pt
                #T = ──── x t [km echivalenti]
                #    100

                record.km_echivalent = record.km * record.categorie_drum_id.valoare
                record.name = "%skm - %s" % (record.km, record.categorie_drum_id.name)

class parcurs_drum_traseu(models.Model):
    _name = 'fleet_fpz.parcurs_drum_traseu'

    name = fields.Char('Localitate')
    localitate_start = fields.Char('Localitate Start')
    localitate_stop = fields.Char('Localitate Stop')
    data_start = fields.Datetime('Data Start')
    data_stop = fields.Datetime('Data Stop')
    lat_start = fields.Float('Latitude Start')
    lon_start = fields.Float('Longitude Start')
    lat_stop = fields.Float('Latitude Stop')
    lon_stop = fields.Float('Longitude Stop')
    dist = fields.Float('Distanta')
    viteza = fields.Float('Viteza')
    total_stationare = fields.Float('Total stationare')
    alarme = fields.Char('Alarme')
    foaie_de_parcurs_id = fields.Many2one('fleet_fpz.foaie_de_parcurs', 'Foaie de parcurs')

    def _compute_name(self):
        for record in self:
            return "%s - %s [%s - %s]" % (record.localitate_start, record.localitate_stop, record.data_start, record.data_stop)

class foaie_de_parcurs(models.Model):
    _name = 'fleet_fpz.foaie_de_parcurs'
    _order = 'date desc' # optional

    name = fields.Char(compute="_compute_name", store=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ],default='draft')
    numar = fields.Char('Numar')
    date = fields.Date('Data', required=True)
    driver_id = fields.Many2one('res.partner', 'Sofer')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Masina', required=True)
    fuel_pump = fields.Float('Pompa')
    fuel_bcf = fields.Float('BCF')
    fuel_advance = fields.Float('Avans')
    fuel_total = fields.Float('Total combustibil', compute="_compute_total_fuel", store=True)
    index_km_start = fields.Float('Plecare')
    index_km_stop = fields.Float('Sosire')
    index_km_total = fields.Float('Total parcurs', required=True, compute="_compute_total_km", store=True)
    km_unknown = fields.Integer('Km necontorizati')
    gm = fields.Float('Sarcina medie (Tone)')
    road_categories = fields.One2many(
        string="Categorii drum",
        comodel_name="fleet_fpz.parcurs_drum",
        inverse_name="foaie_de_parcurs_id"
    )
    trasee = fields.One2many(
        string="Trasee",
        comodel_name="fleet_fpz.parcurs_drum_traseu",
        inverse_name="foaie_de_parcurs_id",
        help="Locul plecari sau sosirii"
    )

    driver_cost = fields.Float(compute="_compute_driver_cost", string="Cost sofer")
    km_de_specificat = fields.Float(compute="_compute_unreported_km")

    km_echiv_parcurs = fields.Float(string="Km echiv. parcurs", compute="_compute_echiv")
    km_echiv_incarcat = fields.Float(string="Km echiv. incarcat", compute="_compute_echiv")
    km_echiv_gol = fields.Float(string="Km echiv. gol", compute="_compute_echiv")
    km_echiv_sporuri = fields.Float(string="Km echiv. sporuri", compute="_compute_echiv")
    km_echiv_total = fields.Float(string="Total km echiv.", compute="_compute_echiv")

    nr_porniri_opriri = fields.Integer(string="Nr porniri/opriri")
    timp_local = fields.Float(string="Localitate")
    timp_inter = fields.Float(string="Interurban")
    timp_inc_desc = fields.Float(string="Incarcat/descarcat", help="Timplul detectat cat masina stationa")
    total_work_time = fields.Float(string="Total lucru")

    nr_incalzire_motor = fields.Integer(string="Nr. incalziri motor")
    nr_curse_comb = fields.Integer(string="Nr curse (comb.)")
    rezerva_aer = fields.Boolean(string="Rezerva aer")
    conditii_nefavorabile = fields.Boolean(string="Conditii nefavorabile")

    joja_ant_rezervor = fields.Float('Joja ant. rezervoar')
    joja_rezervor = fields.Float('Joja rezervoar')
    consum_comb = fields.Float('Consum normat litri', strore=True, compute="_compute_cn")
    consum_comb_diference = fields.Float('Diferente', strore=True)

    km_urbani_buc = fields.Integer('Bucuresti', store=True)
    km_urbani_judet = fields.Integer('Municipii/Judet', store=True)
    km_urbani_alte = fields.Integer('Alte orase', store=True)

    km_urbani_buc_coef = fields.Integer()
    km_urbani_judet_coef = fields.Integer()
    km_urbani_alte_coef = fields.Integer()

    km_urbani_buc_cu_remorca = fields.Boolean()
    km_urbani_judet_cu_remorca = fields.Boolean()
    km_urbani_alte_cu_remorca = fields.Boolean()

    km_urbani_buc_echiv = fields.Float()
    km_urbani_judet_echiv = fields.Float()
    km_urbani_alte_echiv = fields.Float()

    total_km_echiv = fields.Float('Total Km echivalenti')

    @api.multi
    def approve_selected(self):
        for record in self:
            record.approve_button()

    @api.one
    def approve_button(self):
        for record in self:
            if not record.driver_id:
                raise ValidationError(_("Va rugam sa selectati soferul pentru a putea crea costurile"))
        #create costs and fuel logs
        self.env['fleet.vehicle.log.fuel'].create({
            'vehicle_id': record.vehicle_id.id,
            'liter': self.fuel_total,
            'inv_ref': self.numar,
            'notes': 'Alimentare detectate automat',
            'date': self.date})
        self.env.cr.commit()
        self.write({
           'state': 'approved'
        })
    @api.multi
    def act_show_log_cost(self):
        """ This opens log view to view and add new log for this vehicle, groupby default to only show effective costs
            @return: the costs log view
        """
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('fleet', 'fleet_vehicle_costs_action')
        res.update(
            context=dict(self.env.context, default_vehicle_id=self.id, search_default_parent_false=True),
            domain=[('vehicle_id', '=', self.vehicle_id.id), ('date', '=', self.date)]
        )
        return res

    def _compute_driver_cost(self):
        for record in self:
            record.driver_cost = self.timp_local * 3 + self.timp_inter * 4.8 + self.total_work_time * 0.089 + self.nr_porniri_opriri * 0.21 + self.nr_porniri_opriri * 0.77

    @api.depends('road_categories','index_km_total')
    def _compute_unreported_km(self):
        for record in self:
            if record.index_km_total and record.road_categories:
                record.km_de_specificat = record.index_km_total - sum(drum.km for drum in record.road_categories)
                record.km_de_specificat = record.km_de_specificat if record.km_de_specificat >= 1 else 0

    @api.depends('fuel_pump','fuel_bcf', 'fuel_advance')
    def _compute_total_fuel(self):
        for record in self:
            if record.fuel_pump or record.fuel_bcf or record.fuel_advance:
                record.fuel_total = record.fuel_pump + record.fuel_bcf + record.fuel_advance

    @api.depends('index_km_stop','index_km_start')
    def _compute_total_km(self):
        for record in self:
            if record.index_km_stop and record.index_km_start:
                record.index_km_total = record.index_km_stop - record.index_km_start + record.km_unknown

    @api.depends('numar','vehicle_id')
    def _compute_name(self):
         for record in self:
            record.name = "%s / %s" % (record.numar, record.vehicle_id.license_plate)

    @api.depends('joja_ant_rezervor','joja_rezervor','fuel_pump','km_echiv_parcurs', 'km_urbani_buc_cu_remorca', 'km_urbani_judet_cu_remorca', 'km_urbani_alte_cu_remorca', 'gm', 'km_urbani_buc', 'km_urbani_judet', 'km_urbani_alte')
    def _compute_cn(self):
        for record in self:
            #Coeficientul de corectie "A" are valoarea 1,1 si se aplica de regula in perioada 1 decembrie - 15 martie.
            #record_date = datetime.date.strftime(record.date, "%Y-%m-%d")
            #print "faz date %s" % record_date

            #a = 1.1 if record.conditii_nefavorabile or (1, 12) <= (record_date.day, record_date.month) <= (15, 3) else 1
            a = 1.1 if record.conditii_nefavorabile else 1
            self._compute_km_coef()
            #       Pe
            #Cn = ---- x Cmg x KG x A x Sb + Q [litri]
            #      100
            #Pe = Ped + T + U + I +/- Ra [km echivalenti]
            #Ped = Suma de la i=1 pina la 6 Pi x Di [km echivalenti]
            #     Pt
            #T = ---- x t [km echivalenti]
            #     100
            #     Pu
            #U = ---- x u [km echivalenti]
            #     100
            #I = np x i [km echivalenti]
            #      Pa
            #Ra = ---- x ra [km echivalenti]
            #     100
            #Cmg = a se calcula
            #              Cr
            #Sb = -----------------------
            #       Pe/100 x Cmv x KG x A
            #Sporul de consum combustibil pentru opriri si demarari repetate (Q1)
            #             Cm
            #Q1 = 0,25 x ------nod [litri]
            #            100
            #Sporul de consum combustibil pentru insotirea combinei (Q2)
            #Q2 = 0,1 x Cm x nc [litri]
            #Sporul de consum combustibil pentru actionarea instalatiilor speciale (Q3)
            #Q3 = np x qi [litri]
            #Sporul de consum combustibil pentru incalzirea motoarelor pe timp de iarna (Q4)
            #Q4 = 0,05 x Cm x ni [litri]
            #Sporul de consum combustibil pentru formarea rezervei de aer (Q5)
            #Q5 = 0,025 x Cm [litri]
            ped = sum(drum.km_echivalent for drum in record.road_categories)
            print "ped=%s" % ped
            t = 0 #Sporul pentru tractare (T)
            if record.km_urbani_buc_cu_remorca and record.vehicle_id.spor_tractare_remorca1:
                t = (record.km_urbani_buc / 100) * (record.vehicle_id.spor_tractare_remorca1)
            if record.km_urbani_judet_cu_remorca and record.vehicle_id.spor_tractare_remorca1:
                t = (record.km_urbani_judet / 100) * (record.vehicle_id.spor_tractare_remorca1)
            if record.km_urbani_alte_cu_remorca and record.vehicle_id.spor_tractare_remorca1:
                t = (record.km_urbani_alte / 100) * (record.vehicle_id.spor_tractare_remorca1)

            print "t=%s" % t
            record.km_urbani_buc_echiv = (float(record.km_urbani_buc) / 100) * (record.km_urbani_buc_coef)
            record.km_urbani_judet_echiv = (float(record.km_urbani_judet) / 100) * (record.km_urbani_judet_coef)
            record.km_urbani_alte_echiv = (float(record.km_urbani_alte) / 100) * (record.km_urbani_alte_coef)
            u = record.km_urbani_buc_echiv + record.km_urbani_judet_echiv + record.km_urbani_alte_echiv
            print "buc=%s, judet=%s, alte=%s, U=%s" % (record.km_urbani_buc_echiv, record.km_urbani_judet_echiv, record.km_urbani_alte_echiv, u)
            pe = ped + t + u
            cm = record.vehicle_id.cm if record.vehicle_id.cm else self._compute_cm()

            #peste 1.5 tone
            if record.vehicle_id.sarcina_utila_nominala > 1.5:
                consum = (pe / 100) * cm * (record.gm if record.gm else 1) / cm * a
                print consum
            else:
                #sub 1.5 tone
                consum = (pe / 100) * cm  * a
                print consum
            #Cr, reprezinta consumul de combustibil realizat pentru parcurgerea intregului traseu la care exista conditii speciale de exploatare (litri);
            #cr =
            #sb = cr / consum if consum > 0 else 0
            q = 0.025 * (cm /100) * record.nr_porniri_opriri if record.nr_porniri_opriri > 0 else 0

            #consum = consum * sb + q
            consum = consum + q
            #print "consum nominal %s" % cn
            record.total_km_echiv = u
            record.consum_comb = consum
            record.consum_comb_diference = (record.joja_ant_rezervor - record.joja_rezervor) - consum if record.joja_rezervor and record.joja_ant_rezervor else 0
            record.km_echiv_total = ped

    def _compute_cr(self):
        return 1
    def _compute_cm(self):
        return 10
    def _compute_km_coef(self):
        for record in self:
            record.km_urbani_buc_coef = (record.vehicle_id.spor_buc_cu_remorca if record.km_urbani_buc_cu_remorca else record.vehicle_id.spor_buc)
            record.km_urbani_judet_coef = (record.vehicle_id.spor_judet_cu_remorca if record.km_urbani_judet_cu_remorca else record.vehicle_id.spor_judet)
            record.km_urbani_alte_coef = (record.vehicle_id.spor_alte_cu_remorca if record.km_urbani_alte_cu_remorca else record.vehicle_id.spor_alte)

    @api.depends('road_categories.km', 'road_categories.incarcat', 'road_categories.categorie_drum_id')
    def _compute_echiv(self):
        for record in self:
            if record.road_categories:
                record.km_echiv_parcurs = sum(drum.km for drum in record.road_categories)
                record.km_echiv_incarcat = sum(drum.km for drum in record.road_categories if drum.incarcat)
                record.km_echiv_gol = sum(drum.km for drum in record.road_categories if not drum.incarcat)

    @api.model
    def create(self, vals):
        if not vals:
            vals = {}
        vals['numar'] = self.env['ir.sequence'].next_by_code('fleet_fpz.foaie_de_parcurs_nr')
        return super(foaie_de_parcurs, self).create(vals)
