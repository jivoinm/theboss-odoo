# -*- coding: utf-8 -*-
from odoo import http

class Agro(http.Controller):
    @http.route('/agro/agro/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/agro/agro/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('agro.listing', {
            'root': '/agro/agro',
            'objects': http.request.env['agro.agro'].search([]),
        })

    @http.route('/agro/agro/objects/<model("agro.agro"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('agro.object', {
            'object': obj
        })
