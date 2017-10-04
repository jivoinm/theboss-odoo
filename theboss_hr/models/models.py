# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging, datetime

_logger = logging.getLogger(__name__)

class TheBossRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    max_days_waiting = fields.Integer(string="Notificare in", help="Nr de zile pana de la aplicare pana cel responsabil va fi notificat pentru actiune.")
    
    email_template_id = fields.Many2one(
        string=u'Email Template',
        comodel_name='mail.template',
        ondelete='set null',
    )
    
    _
class TheBossApplicant(models.Model):
    _inherit = 'hr.applicant'
    _mail_mass_mailing = _('Job Applicants')

    @api.multi
    def write(self, vals):
       	#add some custom logic
        res = super(TheBossApplicant, self).write(vals)
        # if data['stage_id'] and data['last_stage_id']:
        #     if data['last_stage_id'] > data['stage_id']:
        #         raise UserError(_("Invalid movement!!!"))
        return res

    @api.model
    def write_message(self, message):
        print 'write_message........'
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
        print 'applicants_older_than_job'
        #search for applications older then configured value
        for stage in self.env['hr.recruitment.stage'].search([('max_days_waiting','>', 0)]):
            if stage.email_template_id:
                nr_days = stage.max_days_waiting
                since_date = (datetime.date.today()-datetime.timedelta(days=nr_days)).strftime('%Y-%m-%d')
                applicants_waiting = self.env['hr.applicant'].search([(('date_last_stage_update', '<=', since_date))])
                for applicant in applicants_waiting:
                    alert_user_id = applicant.department_id.manager_id.user_id.id \
                            if applicant.department_id and applicant.department_id.manager_id else applicant.user_id.id
                    if alert_user_id:
                        post_vars = {'partner_ids': [(4, alert_user_id)],}
                        applicant.message_post_with_template(stage.email_template_id.id, **post_vars)