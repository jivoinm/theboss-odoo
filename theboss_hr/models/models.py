# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging, datetime
import json

_logger = logging.getLogger(__name__)

class TheBossRecruitmentJob(models.Model):
    _inherit = "hr.job"
      
    stage_interviews = fields.One2many(
        string=u'Job Interviews',
        comodel_name='theboss_hr.stage_interview',
        inverse_name='job_id'
    )
    
    stage_tasks = fields.One2many(
        string=u'Job Tasks',
        comodel_name='theboss_hr.stage_task',
        inverse_name='job_id'
    )

    @api.multi
    def action_get_stage_interviews_tree_view(self):
        action = self.env.ref('theboss_hr.theboss_hr_stage_interview_view_tree').read()[0]
        print(action)
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.ids[0]
        }
        action['search_view_id'] = (self.env.ref('theboss_hr.theboss_hr_stage_interview_view_tree').id, )
        action['domain'] = ['|', '&', ('res_model', '=', 'hr.job'), ('res_id', 'in', self.ids), '&', ('res_model', '=', 'hr.job'), ('res_id', 'in', self.mapped('application_ids').ids)]

        return action
    
class TheBossRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    max_days_waiting = fields.Integer(string="Notificare in", help="Nr de zile pana de la aplicare pana cel responsabil va fi notificat pentru actiune.")
    
    email_template_id = fields.Many2one(
        string=u'Email Template',
        comodel_name='mail.template',
        ondelete='set null',
    )

    stage_interviews = fields.One2many(
        string=u'Job Interviews',
        comodel_name='theboss_hr.stage_interview',
        inverse_name='stage_id'
    )
    
    stage_tasks = fields.One2many(
        string=u'Job Tasks',
        comodel_name='theboss_hr.stage_task',
        inverse_name='stage_id'
    )

class TheBossStageInterview(models.Model):
    _name = 'theboss_hr.stage_interview'
    
    name = fields.Char('Name', required=True)
    stage_id = fields.Many2one('hr.recruitment.stage', string="Stage", required=True)
    survey_id = fields.Many2one('survey.survey', string="Survey", required=True)

    job_id = fields.Many2one(
        string=u'Job',
        comodel_name='hr.job',
        ondelete='set null',
    )

class TheBossStageTask(models.Model):
    """ This model will store the list of predefined tasks to be stored per a job and a stage
    """

    _name = 'theboss_hr.stage_task'
    _description = u'This model will store the list of predefined tasks to be stored per a job and a stage'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char('Title', required=True)
    stage_id = fields.Many2one('hr.recruitment.stage', string="Stage", required=True)
    activity_type_id = fields.Many2one('mail.activity.type', 'Activity')
    job_id = fields.Many2one(
        string=u'Job',
        comodel_name='hr.job',
        ondelete='set null',
    )


class TheBossStageInterviewResponse(models.Model):
    _name = 'theboss_hr.stage_interview_response'
    
    stage_interview_id = fields.Many2one('theboss_hr.stage_interview', string="Stage Interview")
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response")
    #score = fields.Float(string=u'Score')
    
    applicant_id = fields.Many2one(
        string=u'Applicant',
        comodel_name='hr.applicant',
        ondelete='set null',
    )
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
    
    # @api.onchange('stage_id')
    # def check_if_tasks_are_done(self):
    #     return {
    #                 #'domain': {'other_id': [('partner_id', '=', partner_id)]},
    #                 'warning': {'title': "Warning", 'message': "What is this?"},
    #            }
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


# class TheBossMailActivity(models.Model):
    
#     _inherit = ['mail.activity']

#     @api.depends('res_model', 'res_id')
#     def _compute_res_name(self):
#         for activity in self:
#             print("_compute_res_name res_model=%s res_id=%s" % (activity.res_model, activity.res_id))
#             res_name = self.env[activity.res_model].browse(activity.res_id).name_get()
#             print(res_name)
#             activity.res_name = res_name
    