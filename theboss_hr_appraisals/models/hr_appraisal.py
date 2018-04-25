# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from werkzeug import urls
import logging, datetime
import json
import base64
import lxml.html

_logger = logging.getLogger(__name__)


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    appraisal_id = fields.Many2one(
        string=u'Appraisal',
        comodel_name='hr.appraisal',
        ondelete='set null',
    )
    
class hr_appraisal(models.Model):
    """ Appraisal model
    """
    _name = 'hr.appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = u'Appraisal model'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string=u'Name',
        compute='_compute_name'
    )
    
    active = fields.Boolean(
        string=u'Active',
        default=True,
    )
    
    create_uid = fields.Many2one(
        string=u'Created by',
        comodel_name='res.users',
        default=lambda self: self.env.user
    )

    create_date = fields.Date(
        string=u'Created date',
        default=fields.Date.context_today,
    )

    date_close = fields.Date(
        string=u'Closed date',
    )

    company_id = fields.Many2one(
        string=u'Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.user.company_id
    )
    
    department_id = fields.Many2one(
        string=u'Department',
        comodel_name='hr..department',
        ondelete='set null',
    )
    
    mail_template_id = fields.Many2one(
        string=u'Email Template for appraisal',
        comodel_name='mail.template',
        ondelete='set null',
    )

    meeting_id = fields.Many2one(
        string=u'Calendar event',
        comodel_name='calendar.event',
        ondelete='set null',
    )
    
    
    employee_id = fields.Many2one(
        string=u'Employee',
        comodel_name='hr.employee'
    )
    
    deadline = fields.Date(
        string=u'Deadline'
    )
    
    date_final_interview = fields.Date(
        string=u'Final interview'
    )

    action_plan = fields.Text(
        string=u'Action plan',
    )
        
    manager_appraisal = fields.Boolean(
        string=u'Manager',
    )
    
    manager_ids = fields.One2many(
        string=u'Managers',
        comodel_name='hr.employee',
        inverse_name='appraisal_id',
    )
    
    manager_survey_id = fields.Many2one(
        string=u'Appreisal form',
        comodel_name='survey.survey',
        ondelete='set null',
    ) 
    
    state = fields.Selection(
        string=u'State',
        selection=[('new', 'To Start'), ('pending', 'Sent'),  ('done', 'Done')],
        default='new',
        readonly=True,
    )
    
    count_completed_survey = fields.Integer(
        string=u'Answers',        
        compute='_compute_count_completed_survey'
    )
    
    count_sent_survey = fields.Integer(
        string=u'Sent Appraisals',      
        compute='_compute_count_sent_survey'
    )
        
    color = fields.Text(
        string=u'Color',
    )
        
    @api.multi
    def button_send_appraisal(self):
        self.ensure_one()
        #send email to users
        for manager in self.manager_ids:
            response = self.env['survey.user_input'].create({'survey_id': self.manager_survey_id.id, 'partner_id': manager.user_id.partner_id.id, 'appraisal_id': self.id})
            if self.mail_template_id and self.manager_survey_id:
                self.send_mail(self.mail_template_id, self.manager_survey_id, response.token, None, manager)

        #create responses
        self.write({'state': 'pending'})
    
    @api.multi
    def button_done_appraisal(self):
        self.write({'state': 'done'})

    @api.multi
    def button_cancel_appraisal(self):
        self.write({'state': 'new'})
    
    @api.depends('employee_id')
    def _compute_name(self):
        for record in self:
            record.name = record.employee_id.name
    
   
    @api.depends('manager_survey_id')
    def _compute_count_completed_survey(self):
        AppraisalSurveyAnswer = self.env['survey.user_input']
        for record in self:
            record.count_completed_survey = AppraisalSurveyAnswer.search_count([('appraisal_id', '=', record.id), ('state', '=', 'done')])


    @api.depends('manager_survey_id')
    def _compute_count_sent_survey(self):
        AppraisalSurveyAnswer = self.env['survey.user_input']
        for record in self:
            record.count_sent_survey = AppraisalSurveyAnswer.search_count([('appraisal_id', '=', record.id), ('state', '=', 'new')])

    @api.multi
    def action_get_users_input(self):
        self.ensure_one()
        answers = self.env.context.get('answers')
        res = self.env['ir.actions.act_window'].for_xml_id('theboss_hr_appraisals', 'action_hr_appraisal_responses_act_window')
        res.update(
            context=dict(self.env.context),
            domain=[('appraisal_id', '=', self.id), ('state', '=', 'done' if answers else 'new')]
        )
        return res

    @api.multi
    def action_create_calendar_event(self):
        """ This opens Meeting's calendar view to schedule meeting on current appraisal
            @return: Dictionary value for created Meeting view
        """
        self.ensure_one()
        partners = self.employee_id.user_id.partner_id

        category = self.env.ref('theboss_hr_appraisals.categ_meet_appraisal_interview')
        res = self.env['ir.actions.act_window'].for_xml_id('calendar', 'action_calendar_event')
        res['context'] = {
            'search_default_partner_ids': self.employee_id.name,
            'default_partner_ids': partners.ids,
            'default_user_id': self.env.uid,
            'default_name': self.name,
            'default_categ_ids': category and [category.id] or False,
        }
        return res

    def send_mail(self, template, survey, token, partner_id, employee):
            """ Create one mail by recipients and replace __URL__ by link with identification token """
            Mail = self.env['mail.mail'].with_context({'employee': employee})
            #set url
            url = survey.public_url

            url = urls.url_parse(url).path[1:]  # dirty hack to avoid incorrect urls

            if token:
                url = url + '/' + token

            # post the message
            values = {
                'model': 'hr.appraisal',
                'res_id': self.id,
                'subject': template.subject,
                'body': template.body_html.replace("__URL__", url),
                'body_html': template.body_html.replace("__URL__", url),
                'parent_id': None,
                'attachment_ids': template.attachment_ids and [(6, 0, template.attachment_ids.ids)] or None,
                'email_from': template.email_from or None,
                'auto_delete': True,
                'employee': employee
            }
            if partner_id:
                values['recipient_ids'] = [(4, partner_id)]
            else:
                values['email_to'] = employee.work_email
            Mail.with_context(employee = employee).create(values).send()
            #template.send_mail(template.id, email_values=values)
class hr_appraisal_survey_response(models.Model):
    _inherit = 'survey.user_input'

    appraisal_id = fields.Many2one('hr.appraisal', string="Appraisal")

class hr_appraisal_calendar_event(models.Model):
    _inherit = ['calendar.event']

    @api.multi
    def write(self, vals):
        #add some custom logic
        res = super(hr_appraisal_calendar_event, self).write(vals)
        if self.res_model == 'hr.appraisal' and self.res_id:
            appraisal_object = self.env[self.res_model].browse(self.res_id)
            appraisal_object[0].write({'meeting_id': self.id, 'date_final_interview': self.start_date})
            print("Updated appraisal object with calendar event... %s" % appraisal_object)

        return res
