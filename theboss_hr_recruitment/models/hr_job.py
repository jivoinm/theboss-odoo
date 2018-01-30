# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging, datetime
import json
import base64
import lxml.html

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