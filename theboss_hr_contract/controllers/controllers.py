# -*- coding: utf-8 -*-
from odoo import http

# class FleetFpz(http.Controller):
#     @http.route('/fleet_fpz/fleet_fpz/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_fpz/fleet_fpz/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_fpz.listing', {
#             'root': '/fleet_fpz/fleet_fpz',
#             'objects': http.request.env['fleet_fpz.fleet_fpz'].search([]),
#         })

#     @http.route('/fleet_fpz/fleet_fpz/objects/<model("fleet_fpz.fleet_fpz"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_fpz.object', {
#             'object': obj
#         })