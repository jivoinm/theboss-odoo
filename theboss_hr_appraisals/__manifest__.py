# -*- coding: utf-8 -*-
{
    'name': "The Boss HR Appreisals",

    'summary': """
        HR Employees appraisal,
        Manage employee evaluations and create appraisals""",

    'description': """
        HR Employees appraisal,
        Manage employee evaluations and create appraisals
    """,

    'author': "The Boss Software Management",
    'website': "http://the-boss.ca",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','theboss_hr_contract', 'theboss_hr_document', 'survey', 'l10n_ro'],

    # always loaded
    'data': [
        'security/groups.xml',
        #'security/ir.model.access.csv',
        'views/hr_appraisal_view.xml',
        'views/hr_employee_view.xml',
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
