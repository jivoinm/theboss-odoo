# -*- coding: utf-8 -*-
{
    'name': "The Boss HR",

    'summary': """
        Human Resource Management,
        Process of HR functions in simple way""",

    'description': """
        Human Resource Management,
        Process of HR functions in simple way
    """,

    'author': "The Boss Software Management SRL",
    'website': "http://theboss.go.ro",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.5',

    # any module necessary for this one to work correctly
    'depends': ['base', 'google_drive', 'survey', 'hr', 'hr_recruitment', 'hr_contract', 'hr_holidays', 'hr_payroll_account', 'l10n_ro'],

    # always loaded
    'data': [
        'security/hr_recruitment_survey_security.xml',
        'security/ir.model.access.csv',
        'views/document_template.xml',
        'views/document_template_preview.xml',
        'views/hr_document_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_job_stage_interview_view.xml',
        'views/res_company_view.xml',
        'views/views.xml',
        'views/templates.xml',
        'data/data.xml',
    ],
    #'css': ['static/css/my_css.css'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}
