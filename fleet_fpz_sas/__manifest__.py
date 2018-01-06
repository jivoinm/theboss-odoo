# -*- coding: utf-8 -*-
{
    'name': "The Boss SAS Fleet integration",

    'summary': """
        SAS Fleet integration and GPS sync""",

    'description': """
        Car import from SAS Fleet and GPS sync
    """,

    'author': "The Boss Software Management SRL",
    'website': "http://www.the-boss.ca",
    'category': 'fleet',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'fleet_fpz'],

    # always loaded
    'data': [
        'views/views.xml',
        'data/data.xml',
        'data/scheduled.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
}
