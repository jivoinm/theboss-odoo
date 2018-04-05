# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging, datetime
import json
import base64
import lxml.html

_logger = logging.getLogger(__name__)

class TheBossApplicant(models.Model):
    _inherit = 'hr.applicant'
    _mail_mass_mailing = _('Job Applicants')

    @api.multi
    def write(self, vals):
        #add some custom logic
        res = super(TheBossApplicant, self).write(vals)
        if vals.get('stage_id') and vals.get('stage_id') != self.last_stage_id:
            res_model_id = self.env.ref('hr_recruitment.model_hr_applicant')
            for stage_task in self.stage_id.stage_tasks:
                self.env['mail.activity'].search([('note', '=', stage_task.name), ('res_id', '=', self.id)]).unlink()
                activity = self.env['mail.activity'].create({
                    'activity_type_id': stage_task.activity_type_id.id,
                    'note': stage_task.name,
                    'res_id': self.id,
                    'res_model_id': res_model_id.id,
                })
                activity._onchange_activity_type_id()
        return res

    @api.model
    def write_message(self, message):
        post_vars = {'subject': "Message subject",
                     'body': "Message body",
                     'partner_ids': [(4, 2)],} # Where "4" adds the ID to the list 
                                               # of followers and "3" is the partner ID 
        thread_pool = self.pool.get('mail.thread')
        thread_pool.message_post(
                cr, uid, False,
                type="notification",
                subtype="mt_comment",
                context=context,
                **post_vars)

    @api.model
    def applicants_older_than_job(self):
        #search for applications older then configured value
        for stage in self.env['hr.recruitment.stage'].search([('max_days_waiting','>', 0)]):
            print('stage %s has max_days_waiting = %s with templateid=%s' % (stage.name, stage.max_days_waiting,stage.email_template_id))
            if stage.email_template_id:
                nr_days = stage.max_days_waiting
                since_date = (datetime.date.today()-datetime.timedelta(days=nr_days)).strftime('%Y-%m-%d')
                
                applicants_waiting = self.env['hr.applicant'].search([(('date_last_stage_update', '<=', since_date))])
                print('nr_days=%d since_date=%s applicants_waiting=%d' % (nr_days, since_date, len(applicants_waiting)))
                for applicant in applicants_waiting:
                    alert_user_id = applicant.department_id.manager_id.user_id.id \
                            if applicant.department_id and applicant.department_id.manager_id else applicant.user_id.id
                    if alert_user_id:
                        post_vars = {'partner_ids': [(4, alert_user_id)],}
                        applicant.message_post_with_template(stage.email_template_id.id, **post_vars)
    
    stage_interview_response_ids = fields.One2many(
        string=u'Job Interviews',
        comodel_name='theboss_hr.stage_interview_response',
        inverse_name='applicant_id'
    )

    stage_interview_id = fields.Many2one('theboss_hr.stage_interview', store=False, compute='_compute_stage_interview_id', string="Survey")
    response_id = fields.Many2one('survey.user_input', store=False, compute='_compute_response_id', string="Response")
    score = fields.Float(string=u'Score', store=False, compute='_compute_stage_score')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.applicant')], string='Attachments', ondelete='set null')

    # @api.onchange('stage_id')
    # def check_if_tasks_are_done(self):
    #     undone_tasks = self.env['mail.activity'].search([('res_id', '=', self.id)])
    #     print("undone_tasks=%s, first=%s" % (undone_tasks, undone_tasks[0]))
    #     if undone_tasks:
    #         return {
    #                 #'domain': {'other_id': [('partner_id', '=', partner_id)]},
    #                 'warning': {'title': "Warning", 'message': "Sunt activitati de finalizat, continuati?"},
    #             }
    #     return {}
    @api.depends('stage_id')
    def _compute_stage_interview_id(self):
        for record in self:
            record.stage_interview_id = None
            for stage in record.stage_id.stage_interviews:
                if stage.stage_id == record.stage_id:
                    record.stage_interview_id = stage.id
            
    @api.depends('stage_id')
    def _compute_response_id(self):
        for record in self:
            record.response_id = None
            for response in record.stage_interview_response_ids:
                if response.stage_interview_id.stage_id == record.stage_id:
                    record.response_id = response.response_id

    @api.depends('response_id')
    def _compute_stage_score(self):
        for record in self:
            for response in record.stage_interview_response_ids:
                if response.stage_interview_id.stage_id == record.stage_id:
                    if response.response_id.token:
                        previous_answers = self.env['survey.user_input_line'].sudo().search([('user_input_id.token', '=', response.response_id.token)])
                        # Compute score for each question
                        for answer in previous_answers:
                            record.score = record.score + answer.quizz_mark
                        

    @api.multi
    def action_start_survey(self):
        self.ensure_one()
        # create a response and link it to this applicant        
        if not self.response_id:
            response = self.env['survey.user_input'].create({'survey_id': self.stage_interview_id.survey_id.id, 'partner_id': self.partner_id.id})
            self.env['theboss_hr.stage_interview_response'].create({'stage_interview_id': self.stage_interview_id.id, 'response_id': response.id, 'applicant_id': self.id})
        else:
            response = self.response_id
        # grab the token of the response and start surveying
        return self.stage_interview_id.survey_id.with_context(survey_token=response.token).action_start_survey()
    
    @api.multi
    def action_print_survey(self):
        """ If response is available then print this response otherwise print survey form (print template of the survey) """
        self.ensure_one()
        if not self.response_id:
            return self.action_start_survey()
        else:
            return self.response_id.action_view_answers()

    @api.multi
    def action_generate_documents(self):
        self.ensure_one()
        attachment_ids = self.env['hr.document'].generate_document_attachements(self, 'hr.applicant')
        self.write({'attachment_ids': [(2, 0, attachment_ids)]})
        return True
    