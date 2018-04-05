# -*- coding: utf-8 -*-
{
    'name': "The Boss HR Contracts",

    'summary': """
        HR contracts,
        Manage employee contract with Romanian adaptation""",

    'description': """
        HR contracts,
        Manage employee contract with Romanian adaptation
    """,

    'author': "The Boss Software Management",
    'website': "http://the-boss.ca",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_recruitment', 'hr_contract', 'theboss_hr_document'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_view.xml',
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
