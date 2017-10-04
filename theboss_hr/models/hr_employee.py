# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta, date
from odoo.addons.google_account.models.google_service import GOOGLE_TOKEN_ENDPOINT, TIMEOUT

import json
import re
import urllib2
import werkzeug.urls

# luat de pe wikipedia:
# http://ro.wikipedia.org/wiki/Cod_numeric_personal#JJ
pob = {
    '01': u'Alba',
    '02': u'Arad',
    '03': u'Argeș',
    '04': u'Bacău',
    '05': u'Bihor',
    '06': u'Bistrița-Năsăud',
    '07': u'Botoșani',
    '08': u'Brașov',
    '09': u'Brăila',
    '10': u'Buzău',
    '11': u'Caraș-Severin',
    '12': u'Cluj',
    '13': u'Constanța',
    '14': u'Covasna',
    '15': u'Dâmbovița',
    '16': u'Dolj',
    '17': u'Galați',
    '18': u'Gorj',
    '19': u'Harghita',
    '20': u'Hunedoara',
    '21': u'Ialomița',
    '22': u'Iași',
    '23': u'Ilfov',
    '24': u'Maramureș',
    '25': u'Mehedinți',
    '26': u'Mureș',
    '27': u'Neamț',
    '28': u'Olt',
    '29': u'Prahova',
    '30': u'Satu Mare',
    '31': u'Sălaj',
    '32': u'Sibiu',
    '33': u'Suceava',
    '34': u'Teleorman',
    '35': u'Timiș',
    '36': u'Tulcea',
    '37': u'Vaslui',
    '38': u'Vâlcea',
    '39': u'Vrancea',
    '40': u'București',
    '41': u'București S.1',
    '42': u'București S.2',
    '43': u'București S.3',
    '44': u'București S.4',
    '45': u'București S.5',
    '46': u'București S.6',
    '51': u'Călărași',
    '52': u'Giurgiu',
}

def calc_check_digit(number):
    """Calculate the check digit for personal codes. The number passed
    should not have the check digit included."""
    # note that this algorithm has not been confirmed by an independent source
    weights = (2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9)
    check = sum(w * int(n) for w, n in zip(weights, number)) % 11
    return '1' if check == 10 else str(check)

def get_birth_date(number):
    print "get_birth_date %s" % number
    """Split the date parts from the number and return the birth date."""
    centuries = {
        '1': 1900, '2': 1900, '3': 1800, '4': 1800, '5': 2000, '6': 2000,
    }  # we assume 1900 for the others in order to try to construct a date
    year = int(number[1:3]) + centuries.get(number[0], 1900)
    month = int(number[3:5])
    day = int(number[5:7])
    try:
        return date(year, month, day)
    except ValueError:
        raise InvalidComponent()

def validate(number):
    print "validate %s" % number
    """Checks to see if the number provided is a valid VAT number. This checks
    the length, formatting and check digit."""
    #number = compact(number)
    # first digit should be a known one (9=foreigner)
    if not number.isdigit() or number[0] not in '1234569':
        raise InvalidFormat()
    if len(number) != 13:
        raise InvalidLength()
    # check if birth date is valid
    birth_date = get_birth_date(number)
    # TODO: check that the birth date is not in the future
    # number[7:9] is the county, we ignore it for now, just check last digit
    if calc_check_digit(number[:-1]) != number[-1]:
        raise InvalidChecksum()
    return number


def validate_cnp(number):
    print "validate_cnp %s" % number
    """Checks to see if the number provided is a valid VAT number. This checks
    the length, formatting and check digit."""
    try:
        return bool(validate(number))
    except ValidationError:
        return False


class hr_employee_related(models.Model):
    _name = 'hr.employee.related'
    _description = "Employee person in care or are coinsured"

    # @api.one
    # @api.onchange('ssnid')
    # @api.constrains('ssnid')
    # def _validate_ssnid(self):
    #     if self.ssnid and not validate_cnp(self.ssnid):
    #         raise UserError(_('Invalid SSN number'))

    @api.one
    @api.depends('name')
    def _first_name(self):
        try:
            self.first_name = ' '.join(self.name.split()[:-1])
        except:
            self.first_name = ''

    @api.one
    @api.depends('name')
    def _last_name(self):
        try:
            self.last_name = self.name.split()[-1]
        except:
            self.first_name = ''

    @api.one
    @api.constrains('relation', 'relation_type')
    def _validate_relation(self):
        if self.relation_type and self.relation:
            if self.relation_type in (
                    'coinsured', 'both') and not self.relation in (
                    'husband', 'wife', 'parent'):
                raise ValidationError(_("Just parents and husband/wife"))

    first_name = fields.Char('First Name', compute='_first_name', store=False)
    last_name = fields.Char('Last Name', compute='_last_name', store=False)

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    name = fields.Char('Name', required=True, help='Related person name')
    ssnid = fields.Char('SSN No', required=True, help='Social Security Number')
    relation = fields.Selection([('husband', 'Husband'),
                                 ('wife', 'Wife'),
                                 ('parent', 'Parent'),
                                 ('child', 'Child'),
                                 ('firstdegree', 'First degree relationship'),
                                 ('secdegree', 'Second degree relationship')],
                                string='Relation', required=True)
    relation_type = fields.Selection([('in_care', 'In Care'),
                                      ('coinsured', 'Coinsured'),
                                      ('both', 'Both')],
                                     string='Relation type', required=True)


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.one
    @api.depends('person_related')
    def _number_personcare(self):
        self.person_in_care = self.person_related.search_count([
            ('relation_type', 'in', ('in_care', 'both')),
            ('employee_id', '=', self.id),
        ])

    @api.one
    @api.depends('name')
    def _first_name(self):
        try:
            self.first_name = ' '.join(self.name.split()[:-1])
        except:
            self.first_name = ''

    @api.one
    @api.depends('name')
    def _last_name(self):
        try:
            self.last_name = self.name.split()[-1]
        except:
            self.first_name = ''

    # @api.one
    # @api.onchange('ssnid')
    # @api.constrains('ssnid')
    # def _ssnid_birthday_gender(self):
    #     if self.ssnid and self.country_id and 'RO' in self.country_id.code.upper():
    #         if not validate_cnp(self.ssnid):
    #             raise ValidationError('Invalid SSN number')
    #         gender = bp = None
    #         if self.ssnid[7:9] in pob.keys():
    #             bp = pob[self.ssnid[7:9]]
    #         try:
    #             bday = get_birth_date(self.ssnid)
    #         except:
    #             bday = None
    #         if self.ssnid[0] in '1357':
    #             gender = 'male'
    #         elif self.ssnid[0] in '2468':
    #             gender = 'female'
    #         self.write({
    #             'gender': gender,
    #             'birthday': bday,
    #             'place_of_birth': bp
    #         })

    def _medic_exam_expires(self):
        return fields.Date.to_string(date.today() - timedelta(days = 370))

    @api.multi
    def _return_medic_exam_expiring(self):
        return self.search([
            ('active', '=', True),
            ('medic_exam', '>=', self._medic_exam_expires()),
        ])
        
    first_name = fields.Char('First Name', compute='_first_name', store=False)
    last_name = fields.Char('Last Name', compute='_last_name', store=False)
    ssnid_init = fields.Char(
        'Initial SSN No', help='Initial Social Security Number')
    first_name_init = fields.Char('Initial Name')
    last_name_init = fields.Char('Initial First Name')
    casang = fields.Selection([('AB', 'Alba'), ('AR', 'Arad'),
                               ('AG', 'Arges'), ('BC', 'Bacau'),
                               ('BH', 'Bihor'), ('BN', 'Bistrita-Nasaud'),
                               ('CS', 'Caras-Severin'), ('BT', 'Botosani'),
                               ('BR', 'Braila'), ('BV', 'Brasov'),
                               ('BZ', 'Buzau'), ('CL', 'Calarasi'),
                               ('CJ', 'Cluj'), ('CT', 'Constanta'),
                               ('CV', 'Covasna'), ('DB', 'Dambovita'),
                               ('DJ', 'Dolj'), ('GL', 'Galati'),
                               ('GR', 'Giurgiu'), ('GJ', 'Gorj'),
                               ('HR', 'Harghita'), ('HD', 'Hunedoara'),
                               ('IL', 'Ialomita'), ('IS', 'Iasi'),
                               ('IF', 'Ilfov'), ('MM', 'Maramures'),
                               ('MH', 'Mehedinti'), ('MS', 'Mures'),
                               ('NT', 'Neamt'), ('OT', 'Olt'),
                               ('PH', 'Prahova'), ('SJ', 'Salaj'),
                               ('SM', 'Satu Mare'), ('SB', 'Sibiu'),
                               ('SV', 'Suceava'), ('TR', 'Teleorman'),
                               ('TM', 'Timis'), ('TL', 'Tulcea'),
                               ('VS', 'Vaslui'), ('VL', 'Valcea'),
                               ('VN', 'Vrancea'), ('_B',
                                                   'CAS Municipiu Bucuresti'),
                               ('_A', 'AOPSNAJ'), ('_T', 'CASMTCT')],
                              string='Insurance', required=True, default='AB')
    person_related = fields.One2many(
        'hr.employee.related', 'employee_id', 'Related Persons')
    person_in_care = fields.Integer(string='No of persons in care',
                                    compute='_number_personcare',
                                    help='Number of persons in care')
    emit_by = fields.Char('Emmited by')
    emit_on = fields.Date('Emmited on')
    expires_on = fields.Date('Expires on')

    # override fields declared in hr_contract
    medic_exam = fields.Date('Medical Examination Date', index = True)

class TheBossGoogleDrive(models.Model):
    _inherit = "google.drive.config"
    @api.model
    def copy_doc(self, res_id, template_id, name_gdocs, res_model):
        google_web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        access_token = self.get_access_token()
        # Copy template in to drive with help of new access token
        request_url = "https://www.googleapis.com/drive/v2/files/%s?fields=parents/id&access_token=%s" % (template_id, access_token)
        print "request_url %s" % request_url
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        try:
            req = urllib2.Request(request_url, None, headers)
            parents = urllib2.urlopen(req, timeout=TIMEOUT).read()
        except urllib2.HTTPError:
            raise UserError(_("The Google Template cannot be found. Maybe it has been deleted."))
        parents_dict = json.loads(parents)

        record_url = "Click on link to open Record in Odoo\n %s/?db=%s#id=%s&model=%s" % (google_web_base_url, self._cr.dbname, res_id, res_model)
        data = {
            "title": name_gdocs,
            "description": record_url,
            "parents": parents_dict['parents']
        }
        request_url = "https://www.googleapis.com/drive/v2/files/%s/copy?access_token=%s" % (template_id, access_token)
        headers = {
            'Content-type': 'application/json',
            'Accept': 'text/plain'
        }
        data_json = json.dumps(data)
        print "data_json %s" % data_json
        # resp, content = Http().request(request_url, "POST", data_json, headers)
        req = urllib2.Request(request_url, data_json, headers)
        content = urllib2.urlopen(req, timeout=TIMEOUT).read()
        content = json.loads(content)
        res = {}
        if content.get('alternateLink'):
            res['id'] = self.env["ir.attachment"].create({
                'res_model': res_model,
                'name': name_gdocs,
                'res_id': res_id,
                'type': 'url',
                'url': content['alternateLink']
            }).id
            # Commit in order to attach the document to the current object instance, even if the permissions has not been written.
            self._cr.commit()
            res['url'] = content['alternateLink']
            key = self._get_key_from_url(res['url'])
            request_url = "https://www.googleapis.com/drive/v2/files/%s/permissions?emailMessage=This+is+a+drive+file+created+by+Odoo&sendNotificationEmails=false&access_token=%s" % (key, access_token)
            data = {'role': 'writer', 'type': 'anyone', 'value': '', 'withLink': True}
            try:
                req = urllib2.Request(request_url, json.dumps(data), headers)
                urllib2.urlopen(req, timeout=TIMEOUT)
            except urllib2.HTTPError:
                raise self.env['res.config.settings'].get_config_warning(_("The permission 'reader' for 'anyone with the link' has not been written on the document"))
            if self.env.user.email:
                data = {'role': 'writer', 'type': 'user', 'value': self.env.user.email}
                try:
                    req = urllib2.Request(request_url, json.dumps(data), headers)
                    urllib2.urlopen(req, timeout=TIMEOUT)
                except urllib2.HTTPError:
                    pass
        return res