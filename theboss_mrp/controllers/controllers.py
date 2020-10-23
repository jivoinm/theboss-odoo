# -*- coding: utf-8 -*-
# from odoo import http


# class ThebossMrp(http.Controller):
#     @http.route('/theboss_mrp/theboss_mrp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/theboss_mrp/theboss_mrp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('theboss_mrp.listing', {
#             'root': '/theboss_mrp/theboss_mrp',
#             'objects': http.request.env['theboss_mrp.theboss_mrp'].search([]),
#         })

#     @http.route('/theboss_mrp/theboss_mrp/objects/<model("theboss_mrp.theboss_mrp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('theboss_mrp.object', {
#             'object': obj
#         })
