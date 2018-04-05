# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging, datetime
import json
import base64
import lxml.html

_logger = logging.getLogger(__name__)

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
