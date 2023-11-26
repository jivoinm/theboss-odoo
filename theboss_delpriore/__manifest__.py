# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'TheBoss DelPriore Kitchens',
    'version': '17.0',
    'category': 'Hidden',
    'description': """
Custom setup for DelPriore Kitchens.
====================================================================================

It is basically used when we want to keep track of production orders generated
from sales order. It adds sales name and sales Reference on production order.
    """,
    'depends': ['survey','theboss_sale_mrp', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        'views/sale_order_views.xml',
        'views/project_views.xml',
        "data/products.xml",
        "data/product_attributes.xml",
        "data/product_attributes_lines.xml",
        "data/sales_rep_workflow.xml",
        "data/users.xml",
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
