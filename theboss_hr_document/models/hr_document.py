# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel
import base64
import copy
import datetime
import dateutil.relativedelta as relativedelta
import logging

import functools
import lxml
from werkzeug import urls

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import pycompat

_logger = logging.getLogger(__name__)

def format_date(env, date, pattern=False):
    if not date:
        return ''
    date = datetime.datetime.strptime(date[:10], tools.DEFAULT_SERVER_DATE_FORMAT)
    lang_code = env.context.get('lang') or 'en_US'
    if not pattern:
        lang = env['res.lang']._lang_get(lang_code)
        pattern = lang.date_format
    try:
        locale = babel.Locale.parse(lang_code)
        pattern = tools.posix_to_ldml(pattern, locale=locale)
        return babel.dates.format_date(date, format=pattern, locale=locale)
    except babel.core.UnknownLocaleError:
        return date.strftime(pattern)


def format_tz(env, dt, tz=False, format=False):
    record_user_timestamp = env.user.sudo().with_context(tz=tz or env.user.sudo().tz or 'UTC')
    timestamp = datetime.datetime.strptime(dt, tools.DEFAULT_SERVER_DATETIME_FORMAT)

    ts = fields.Datetime.context_timestamp(record_user_timestamp, timestamp)

    # Babel allows to format datetime in a specific language without change locale
    # So month 1 = January in English, and janvier in French
    # Be aware that the default value for format is 'medium', instead of 'short'
    #     medium:  Jan 5, 2016, 10:20:31 PM |   5 janv. 2016 22:20:31
    #     short:   1/5/16, 10:20 PM         |   5/01/16 22:20
    if env.context.get('use_babel'):
        # Formatting available here : http://babel.pocoo.org/en/latest/dates.html#date-fields
        from babel.dates import format_datetime
        return format_datetime(ts, format or 'medium', locale=env.context.get("lang") or 'en_US')

    if format:
        return ts.strftime(format)
    else:
        lang = env.context.get("lang")
        langs = env['res.lang']
        if lang:
            langs = env['res.lang'].search([("code", "=", lang)])
        format_date = langs.date_format or '%B-%d-%Y'
        format_time = langs.time_format or '%I-%M %p'

        fdate = ts.strftime(format_date).decode('utf-8')
        ftime = ts.strftime(format_time).decode('utf-8')
        return "%s %s%s" % (fdate, ftime, (' (%s)' % tz) if tz else '')

def format_amount(env, amount, currency):
    fmt = "%.{0}f".format(currency.decimal_places)
    lang = env['res.lang']._lang_get(env.context.get('lang') or 'en_US')

    formatted_amount = lang.format(fmt, currency.round(amount), grouping=True, monetary=True)\
        .replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'\u2011')

    pre = post = u''
    if currency.position == 'before':
        pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=currency.symbol or '')
    else:
        post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=currency.symbol or '')

    return u'{pre}{0}{post}'.format(formatted_amount, pre=pre, post=post)

try:
     # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment
    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,               # do not output newline after blocks
        autoescape=True,                # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw : relativedelta.relativedelta(*a, **kw),
    })
    mako_safe_template_env = copy.copy(mako_template_env)
    mako_safe_template_env.autoescape = False
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class HRDocument(models.Model):
    "HR Document"
    _name = "hr.document"
    _description = 'HR Document'
    _order = 'name'

    @api.model
    def default_get(self, fields):
        res = super(HRDocument, self).default_get(fields)
        if res.get('model'):
            res['model_id'] = self.env['ir.model'].search([('model', '=', res.pop('model'))]).id
        return res

    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model', 'Applies to', help="The type of document this template can be used with")
    model = fields.Char('Related Document Model', related='model_id.model', index=True, store=True, readonly=True)
    lang = fields.Char('Language',
                       help="Optional translation language (ISO code) to select when sending out an email. "
                            "If not set, the english version will be used. "
                            "This should usually be a placeholder expression "
                            "that provides the appropriate language, e.g. "
                            "${object.partner_id.lang}.",
                       placeholder="${object.partner_id.lang}")

    filter_id = fields.Many2one('ir.filters', 'Filter', domain="[('model_id', '=', model)]")
    
    body_html = fields.Html('Body', translate=True, sanitize=False)
    ref_ir_act_window = fields.Many2one('ir.actions.act_window', 'Sidebar action', readonly=True, copy=False,
                                        help="Sidebar action to make this template available on records "
                                             "of the related document model")
    ref_ir_value = fields.Many2one('ir.values', 'Sidebar Button', readonly=True, copy=False,
                                   help="Sidebar button to open the sidebar action")
    
    # Fake fields used to implement the placeholder assistant
    model_object_field = fields.Many2one('ir.model.fields', string="Field",
                                         help="Select target field from the related document model.\n"
                                              "If it is a relationship field you will be able to select "
                                              "a target field at the destination of the relationship.")
    sub_object = fields.Many2one('ir.model', 'Sub-model', readonly=True,
                                 help="When a relationship field is selected as first field, "
                                      "this field shows the document model the relationship goes to.")
    sub_model_object_field = fields.Many2one('ir.model.fields', 'Sub-field',
                                             help="When a relationship field is selected as first field, "
                                                  "this field lets you select the target field within the "
                                                  "destination document model (sub-model).")
    null_value = fields.Char('Default Value', help="Optional value to use if the target field is empty")
    copyvalue = fields.Char('Placeholder Expression', help="Final placeholder expression, to be copy-pasted in the desired template field.")
    scheduled_date = fields.Char('Scheduled Date', help="If set, the queue manager will send the email after the date. If not set, the email will be send as soon as possible. Jinja2 placeholders may be used.")

    @api.onchange('model_id')
    def onchange_model_id(self):
        # TDE CLEANME: should'nt it be a stored related ?
        if self.model_id:
            self.model = self.model_id.model
        else:
            self.model = False

    def build_expression(self, field_name, sub_field_name, null_value):
        """Returns a placeholder expression for use in a template field,
        based on the values provided in the placeholder assistant.
        :param field_name: main field name
        :param sub_field_name: sub field name (M2O)
        :param null_value: default value if the target value is empty
        :return: final placeholder expression """
        expression = ''
        if field_name:
            expression = "${object." + field_name
            if sub_field_name:
                expression += "." + sub_field_name
            if null_value:
                expression += " or '''%s'''" % null_value
            expression += "}"
        return expression

    @api.onchange('model_object_field', 'sub_model_object_field', 'null_value')
    def onchange_sub_model_object_value_field(self):
        if self.model_object_field:
            if self.model_object_field.ttype in ['many2one', 'one2many', 'many2many']:
                models = self.env['ir.model'].search([('model', '=', self.model_object_field.relation)])
                if models:
                    self.sub_object = models.id
                    self.copyvalue = self.build_expression(self.model_object_field.name, self.sub_model_object_field and self.sub_model_object_field.name or False, self.null_value or False)
            else:
                self.sub_object = False
                self.sub_model_object_field = False
                self.copyvalue = self.build_expression(self.model_object_field.name, False, self.null_value or False)
        else:
            self.sub_object = False
            self.copyvalue = False
            self.sub_model_object_field = False
            self.null_value = False

    @api.multi
    def unlink(self):
        self.unlink_action()
        return super(HRDocument, self).unlink()

    @api.multi
    def copy(self, default=None):
        default = dict(default or {},
                       name=_("%s (copy)") % self.name)
        return super(HRDocument, self).copy(default=default)

    @api.multi
    def unlink_action(self):
        for template in self:
            if template.ref_ir_act_window:
                template.ref_ir_act_window.sudo().unlink()
            if template.ref_ir_value:
                template.ref_ir_value.sudo().unlink()
        return True


    @api.model
    def render_post_process(self, html):
        return html

    @api.model
    def render_template(self, template_txt, model, res_ids, post_process=False):
        """ Render the given template text, replace mako expressions ``${expr}``
        with the result of evaluating these expressions with an evaluation
        context containing:
         - ``user``: Model of the current user
         - ``object``: record of the document record this mail is related to
         - ``context``: the context passed to the mail composition wizard
        :param str template_txt: the template text to render
        :param str model: model name of the document record this mail is related to.
        :param int res_ids: list of ids of document records those mails are related to.
        """
        multi_mode = True
        if isinstance(res_ids, pycompat.integer_types):
            multi_mode = False
            res_ids = [res_ids]

        results = dict.fromkeys(res_ids, u"")

        # try to load the template
        try:
            mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
            template = mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info("Failed to load template %r", template_txt, exc_info=True)
            return multi_mode and results or results[res_ids[0]]

        # prepare template variables
        records = self.env[model].browse(it for it in res_ids if it)  # filter to avoid browsing [None]
        res_to_rec = dict.fromkeys(res_ids, None)
        for record in records:
            res_to_rec[record.id] = record
        variables = {
            'format_date': lambda date, format=False, context=self._context: format_date(self.env, date, format),
            'format_tz': lambda dt, tz=False, format=False, context=self._context: format_tz(self.env, dt, tz, format),
            'format_amount': lambda amount, currency, context=self._context: format_amount(self.env, amount, currency),
            'user': self.env.user,
            'ctx': self._context,  # context kw would clash with mako internals
        }
        for res_id, record in res_to_rec.items():
            variables['object'] = record
            try:
                render_result = template.render(variables)
            except Exception:
                _logger.info("Failed to render template %r using values %r" % (template, variables), exc_info=True)
                raise UserError(_("Failed to render template %r using values %r")% (template, variables))
            if render_result == u"False":
                render_result = u""
            results[res_id] = render_result

        if post_process:
            for res_id, result in results.items():
                results[res_id] = self.render_post_process(result)

        return multi_mode and results or results[res_ids[0]]

    @api.multi
    def get_email_template(self, res_ids):
        multi_mode = True
        if isinstance(res_ids, pycompat.integer_types):
            res_ids = [res_ids]
            multi_mode = False

        if res_ids is None:
            res_ids = [None]
        results = dict.fromkeys(res_ids, False)

        if not self.ids:
            return results
        self.ensure_one()

        langs = self.render_template(self.lang, self.model, res_ids)
        for res_id, lang in langs.items():
            if lang:
                template = self.with_context(lang=lang)
            else:
                template = self
            results[res_id] = template

        return multi_mode and results or results[res_ids[0]]

    @api.multi
    def get_template(self, res_ids, fields=None):
        """Generates the template for given the given model based on
        records given by res_ids.
        :param template_id: id of the template to render.
        :param res_id: id of the record to use for rendering the template (model
                       is taken from template definition)
        :returns: a dict containing all relevant fields for creating a new
                  mail.mail entry, with one extra key ``attachments``, in the
                  format [(report_name, data)] where data is base64 encoded.
        """
        self.ensure_one()
        multi_mode = True
        if isinstance(res_ids, pycompat.integer_types):
            res_ids = [res_ids]
            multi_mode = False
        if fields is None:
            fields = ['body_html']

        res_ids_to_templates = self.get_email_template(res_ids)

        # templates: res_id -> template; template -> res_ids
        templates_to_res_ids = {}
        for res_id, template in res_ids_to_templates.items():
            templates_to_res_ids.setdefault(template, []).append(res_id)

        results = dict()
        for template, template_res_ids in templates_to_res_ids.items():
            Template = self.env['hr.document']
            # generate fields value for all res_ids linked to the current template
            if template.lang:
                Template = Template.with_context(lang=template._context.get('lang'))
            for field in fields:
                Template = Template.with_context()
                generated_field_values = Template.render_template(
                    getattr(template, field), template.model, template_res_ids,
                    post_process=(field == 'body_html'))
                for res_id, field_value in generated_field_values.items():
                    results.setdefault(res_id, dict())[field] = field_value
            # update values for all res_ids
            for res_id in template_res_ids:
                values = results[res_id]
                if values.get('body_html'):
                    values['body'] = tools.html_sanitize(values['body_html'])
                # technical settings
                values.update(
                    model=template.model,
                    res_id=res_id or False,
                )
        return multi_mode and results or results[res_ids[0]]

    def generate_document_attachements(self, model, model_name, file_name_query=None):
        attachment_ids = []
        search_document = [('model', '=', model_name)]
        if file_name_query:
            search_document.append(file_name_query)
        applicant_docs = self.env['hr.document'].search(search_document)
        for doc in applicant_docs:
            values = doc.get_template(model.id)
            report_obj = self.env['ir.actions.report']
            
            IrConfig = self.env['ir.config_parameter'].sudo()
            base_url = IrConfig.get_param('report.url') or IrConfig.get_param('web.base.url')
            html = values['body_html']
            #layout = self.env['ir.ui.view'].browse(self.env['ir.ui.view'].get_view_id('theboss_hr_document.minimal_layout_hr_doc'))
            layout = self.env['ir.ui.view'].browse(self.env['ir.ui.view'].get_view_id('web.external_layout'))
            body = layout.render(dict(subst=True, body=html, base_url=base_url))
            print(body)
            pdf_content = report_obj._run_wkhtmltopdf(
                [body],
            )
            
            result = base64.b64encode(pdf_content)
            Attachment = self.env['ir.attachment'] 
            if Attachment.search_count([('res_id','=', model.id), ('name','=', doc.name), ('res_model', '=', model_name)]) == 0:
                file_name = doc.name
                attachment_data = {
                    'name': file_name,
                    'datas_fname': file_name + '.pdf',
                    'datas': result,
                    'type': 'binary',
                    'res_model': model_name,
                    'res_id': model.id,
                }
                attachment_ids.append(Attachment.create(attachment_data).id)
        return attachment_ids