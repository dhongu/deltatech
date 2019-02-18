# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################


import openerp
from openerp import http

from openerp.http import request, STATIC_CACHE
import time
    
class OData(http.Controller):
    
    @http.route('/OData', type='http', auth='user')
    def get_collections(self, req):
      irm = request.env()['ir.model'].sudo()
      cr, uid, context = request.cr, openerp.SUPERUSER_ID, request.context
      iuv = request.registry['ir.ui.view']
      mimetype ='application/xml;charset=utf-8'
      
      models = irm.search([])
      values = {
            'collections': models,
        }
      
      page = iuv.render(cr, uid,'deltatech_odata.collections', values, context=context)
      

      return request.make_response(page, [('Content-Type', mimetype)])


    @http.route('/OData/<model>', type='http', auth='user')
    def get_model(self, model):
      irm = request.env()['model'].sudo()
      cr, uid, context = request.cr, openerp.SUPERUSER_ID, request.context
      iuv = request.registry['ir.ui.view']
      mimetype ='application/xml;charset=utf-8'
      
      models = irm.search([])
      values = {
            'collections': models,
        }
      
      page = iuv.render(cr, uid,'deltatech_odata.model', values, context=context)
      

      return request.make_response(page, [('Content-Type', mimetype)])



#openerp.addons.website_sale.controllers.main.website_sale = WebsiteSale