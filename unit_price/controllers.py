# -*- coding: utf-8 -*-
from openerp import http

# class TerraUnitprice(http.Controller):
#     @http.route('/terra_unitprice/terra_unitprice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/terra_unitprice/terra_unitprice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('terra_unitprice.listing', {
#             'root': '/terra_unitprice/terra_unitprice',
#             'objects': http.request.env['terra_unitprice.terra_unitprice'].search([]),
#         })

#     @http.route('/terra_unitprice/terra_unitprice/objects/<model("terra_unitprice.terra_unitprice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('terra_unitprice.object', {
#             'object': obj
#         })