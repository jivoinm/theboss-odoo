# -*- coding: utf-8 -*-
{
    'name': "Flota Masini - FAZ",

    'summary': """
        Foi de parcurs zilnice pentru flota de masini""",

    'description': """
        Foi de parcurs zilnice pentru flota de masini
    """,

    'author': "The Boss Software Management SRL",
    'website': "http://www.theboss.go.ro",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'fleet',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'fleet', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/faz_seq.xml',
        'views/views.xml',
        'views/faz_board_view.xml',
        'views/templates.xml',
        'data/data.xml',
    ],
    'css': ['static/css/my_css.css'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}
