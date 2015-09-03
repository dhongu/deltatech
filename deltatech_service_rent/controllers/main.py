# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
##############################################################################

import babel.dates
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import werkzeug.urls
from werkzeug.exceptions import NotFound

from openerp import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

from openerp import SUPERUSER_ID


class website_service(http.Controller):

    @http.route(['/service/equipment', '/service/equipment/page/<int:page>'], type='http', auth="user", website=True)
    def equipments(self, page=1, search='',  **post):
        cr, uid, context = request.cr, request.uid, request.context
        equipment_obj = request.registry['service.equipment']
        
        order = 'name'

        step = 10  # Number of equipment per page

        domain = []
        if search:
            for srch in search.split(" "):
                domain += ['|', '|', '|',
                           ('name', 'ilike', srch), 
                           ('ean_code', '=', srch),
                           ('product_id.name', 'ilike', srch), 
                           ('serial_id.name', '=', srch)]

        
        equipment_count = equipment_obj.search(request.cr, request.uid, domain, count=True, context=request.context)
        
        pager = request.website.pager(
            url="/service/equipment",
            url_args={},
            total=equipment_count,
            page=page,
            step=step,
            scope=5)


        obj_ids = equipment_obj.search( request.cr, request.uid, domain, limit=step,
                                        offset=pager['offset'], order=order, context=request.context)
        
        equipment_ids = equipment_obj.browse(request.cr, request.uid, obj_ids, context=request.context)
        
        values = {
            'search': search,
            'equipment_ids':equipment_ids,
            'pager': pager,
            
        }

        return request.website.render("deltatech_service_rent.equipments", values)


    @http.route(['/service/equipment/<model("service.equipment"):equipment>'], type='http', auth="user", website=True)
    def equipment_page(self, equipment, search='',message='', message_type='', **post):
         
        values = {
            'search': search,
            'equipment': equipment,
            'message': message,
            'message_type':message_type,  # poate fi success, info,  warning, danger
        }
        # alert-success 
        return request.website.render("deltatech_service_rent.equipment", values)

 


    @http.route(['/service/equipment/meter_post/<model("service.meter"):meter>'], type='http', auth="user", methods=['POST'], website=True)
    def meter_post(self, meter, index=0.0, **post):

        values = {
            'search':'',
            'meter': meter,
            'equipment': meter.equipment_id,
            'index': index,
        }
        
        cr, uid, context = request.cr, request.uid, request.context
        
        index = float(index)
        
              
        if index <= meter.total_counter_value:
            values['message_type'] = 'danger'
            values['message'] = _('Input value must be greater than %s') % str(meter.total_counter_value)
            
        else:
            user = request.registry['res.users'].browse(cr,SUPERUSER_ID,uid,context)
            
            request.registry['service.meter.reading'].create(cr,SUPERUSER_ID,{'meter_id':meter.id,
                                                                                 'equipment_id':meter.equipment_id.id,
                                                                                 'read_by':user.partner_id.id,
                                                                                 'counter_value':index},    context)
            values['message_type'] = 'success'
            values['message'] = _('Index was been updated')
        return request.website.render("deltatech_service_rent.equipment", values)




    @http.route(['/service/equipment/notification_post/<model("service.equipment"):equipment>'], type='http', auth="user", methods=['POST'], website=True)
    def notification_port(self, equipment, subject, description, **post):
        notification_obj = request.registry['service.notification']
        
        values = {
           'search':'',
           'equipment': equipment,
           'message_type': 'success',
        }  
        
   
        new_id = notification_obj.create(request.cr,SUPERUSER_ID,{     'subject': subject,
                                                                       'description':description,
                                                                       'from_user_id':request.uid,
                                                                       'equipment_id':equipment.id,  },    request.context)
 
        notification = notification_obj.browse(request.cr, SUPERUSER_ID, new_id, request.context)
        
        values['message'] = _('Notification was posted with number %s') % notification.name
     
        return request.website.render("deltatech_service_rent.equipment", values)


 

    @http.route(['/service/order/<int:order_id>',
                 '/service/order/<int:order_id>/<token>'], type='http', auth="public", website=True)
    def order_page(self, order_id, token=None,  message=False, **post):       
        order = request.registry.get('service.order').browse(request.cr, token and SUPERUSER_ID or request.uid, order_id, request.context)
        if token:
            if token != order.access_token:
                return request.website.render('website.404')      
        
        user = request.registry['res.users'].browse(request.cr,SUPERUSER_ID,request.uid,request.context)
        if user:
            signer = user.name
        else:
            signer = ''
            
        values = {
            'order': order,
            'signer':signer,
            'message': message and int(message) or False,
        }
 
        return request.website.render("deltatech_service_rent.order", values)

    @http.route(['/service/order/accept'], type='json', auth="public", website=True)
    def order_accept(self, order_id, token=None, signer=None, sign=None, **post):
        order_obj = request.registry.get('service.order')
        order = order_obj.browse(request.cr, SUPERUSER_ID, order_id)
        if token != order.access_token:
            return request.website.render('website.404')
        if sign:
            order_obj.write(request.cr, SUPERUSER_ID, order_id, {'signature':sign})
        order_obj.action_done(request.cr, SUPERUSER_ID, [order_id])
        
        return True


    @http.route(['/service/order/<int:order_id>/<token>/decline'], type='http', auth="public", website=True)
    def order_decline(self, order_id, token, **post):
        order_obj = request.registry.get('service.order')
        order = order_obj.browse(request.cr, SUPERUSER_ID, order_id)
        if token != order.access_token:
            return request.website.render('website.404')
        
        message = post.get('decline_message')
        order_obj.action_rejected(request.cr, SUPERUSER_ID, [order_id])
        if message:
            order_obj.message_post(request.cr, SUPERUSER_ID, [order_id], body= message)

        return werkzeug.utils.redirect("/service/order/%s/%s?message=2" % (order_id, token))




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
