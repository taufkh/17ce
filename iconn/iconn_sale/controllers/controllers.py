# -*- coding: utf-8 -*-
# from odoo import http


# class IconnSale(http.Controller):
#     @http.route('/iconn_sale/iconn_sale', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/iconn_sale/iconn_sale/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('iconn_sale.listing', {
#             'root': '/iconn_sale/iconn_sale',
#             'objects': http.request.env['iconn_sale.iconn_sale'].search([]),
#         })

#     @http.route('/iconn_sale/iconn_sale/objects/<model("iconn_sale.iconn_sale"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('iconn_sale.object', {
#             'object': obj
#         })
