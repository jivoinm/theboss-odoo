# -*- coding: utf-8 -*-
{
    'name': "Agro Fields Management",

    'summary': """
        Farm management software""",

    'description': """
        Farm management software
    """,

    'author': "TheBoss Software Management",
    'website': "http://www.thebosssoftware.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Apps',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['base', 'website', 'crm', 'project'],
    'depends': ['base', 'project'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/workflows.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
