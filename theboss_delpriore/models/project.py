# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime
class ProjectTask(models.Model):
    _inherit = "project.task"
    
    project_task_survey_id = fields.Many2one(
        'theboss_delpriore.stage_survey_response',
        string='Project Task Survey',
        )
    
    def _setMOValues(self, mo):
        for project_task in self:
            super(ProjectTask, self)._setMOValues(mo)
            delay = self.env['ir.config_parameter'].get_param('mrp_production_delay_days')
            delay = delay if delay else 4
            mo.order_details = project_task.description
            mo.date_planned_start = project_task.date_deadline - datetime.timedelta(days=delay)

    def action_get_stage_survey_tree_view(self):
        action = self.env.ref('theboss_delpriore.theboss_hr_stage_survey_view_tree').read()[0]
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.ids[0]
        }
        action['search_view_id'] = (self.env.ref('theboss_delpriore.theboss_hr_stage_survey_view_tree').id, )
        action['domain'] = ['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)]

        return action
   
    @api.onchange('stage_id')
    def check_if_tasks_are_done(self):
        self.ensure_one()
        action = {}
        for project_task in self:
            undone_tasks = self.env['mail.activity'].search([('res_model', '=', 'project.task'), ('res_id', '=',  project_task._origin.id)])
            if undone_tasks:
               action = self.show_warning_message("There are some unfinished tasks!")
               project_task.stage_id.id = project_task._origin.stage_id.id
        return action
   

class ProjectTaskType(models.Model):
    _inherit = ['project.task.type']

    max_days_waiting = fields.Integer(string="Max days to notify", help="Nr. of days to notify")
    email_template_id = fields.Many2one(
        string=u'Email Template',
        comodel_name='mail.template',
        ondelete='set null',
    )

    survey_id = fields.Many2one('survey.survey', string="Survey")

class ProjectStageSurveyResponse(models.Model):
    _name = 'theboss_delpriore.stage_survey_response'
   
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response")
    user_id = fields.Many2one('res.users',
        string='Assigned to',
        default=lambda self: self.env.uid,
        index=True, tracking=True)
