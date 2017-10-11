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

from odoo import http
from odoo import tools
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.website.models.website import slug

from odoo import SUPERUSER_ID


class website_service(http.Controller):

    @http.route(['/service/equipments', '/service/equipments/page/<int:page>'], type='http', auth="user", website=True)
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
            url="/service/equipments",
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

        return request.website.render("deltatech_service_website.equipments", values)


    @http.route(['/service/equipment/<model("service.equipment"):equipment>'], type='http', auth="user", website=True)
    def equipment_page(self, equipment, search='',message='', message_type='', **post):
         
        values = {
            'search': search,
            'equipment': equipment,
            'message': message,
            'message_type':message_type,  # poate fi success, info,  warning, danger
        }
        # alert-success 
        return request.website.render("deltatech_service_website.equipment", values)

 


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
        return request.website.render("deltatech_service_website.equipment", values)




    @http.route(['/service/equipment/notification_post/<model("service.equipment"):equipment>'], type='http', auth="user", methods=['POST'], website=True)
    def notification_post(self, equipment, subject, description, **post):
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
     
        return request.website.render("deltatech_service_website.equipment", values)


    @http.route(['/service/notifications', '/service/notifications/page/<int:page>'], type='http', auth="user", website=True)
    def notifications(self, page=1, search='', equipment_id='',  **post):
        cr, uid, context = request.cr, request.uid, request.context
        notification_obj = request.registry['service.notification']
        
        order = 'name'

        step = 10  # Number of order per page

        domain = []
        if search:
            for srch in search.split(" "):
                domain += ['|', '|', '|',
                           ('name', 'ilike', srch), 
                           ('equipment_id.ean_code', '=', srch),
                           ('equipment_id.name', 'ilike', srch)]
        
        if equipment_id:
            equipment_id = int(equipment_id)
            domain += [('equipment_id','=',equipment_id)]
            equipment = request.registry['service.equipment'].browse(request.cr, request.uid, equipment_id, context=request.context)
            
        notification_count = notification_obj.search(request.cr, request.uid, domain, count=True, context=request.context)
        
        pager = request.website.pager(
            url="/service/notifications",
            url_args={},
            total=notification_count,
            page=page,
            step=step,
            scope=5)


        obj_ids = notification_obj.search( request.cr, request.uid, domain, limit=step,
                                        offset=pager['offset'], order=order, context=request.context)
        
        
        notification_ids = notification_obj.browse(request.cr, request.uid, obj_ids, context=request.context)
        
        values = {
            'search': search,
            'notification_ids':notification_ids,
            'pager': pager,
        }
        if equipment_id:
            values['equipment'] = equipment
            
        return request.website.render("deltatech_service_website.notifications", values)


    @http.route(['/service/notification/<model("service.notification"):notification>'], type='http', auth="user", website=True)
    def notification_page(self, notification,  **post):            
        values = {
            'notification': notification,
            'equipment': notification.equipment_id,
        }
        return request.website.render("deltatech_service_website.notification", values)
    

    @http.route(['/service/orders', '/service/orders/page/<int:page>'], type='http', auth="user", website=True)
    def orders(self, page=1, search='',  **post):
        cr, uid, context = request.cr, request.uid, request.context
        order_obj = request.registry['service.order']
        
        order = 'name'

        step = 10  # Number of order per page

        domain = []
        if search:
            for srch in search.split(" "):
                domain += ['|', '|', '|',
                           ('name', 'ilike', srch), 
                           ('equipment_id.ean_code', '=', srch),
                           ('equipment_id.name', 'ilike', srch)]

        
        order_count = order_obj.search(request.cr, request.uid, domain, count=True, context=request.context)
        
        pager = request.website.pager(
            url="/service/orders",
            url_args={},
            total=order_count,
            page=page,
            step=step,
            scope=5)


        obj_ids = order_obj.search( request.cr, request.uid, domain, limit=step,
                                        offset=pager['offset'], order=order, context=request.context)
        
        order_ids = order_obj.browse(request.cr, request.uid, obj_ids, context=request.context)
        
        values = {
            'search': search,
            'order_ids':order_ids,
            'pager': pager,
        }

        return request.website.render("deltatech_service_website.orders", values)
 

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
            'equipment': order.equipment_id,
            'signer':signer,
            'message': message and int(message) or False,
        }
 
        return request.website.render("deltatech_service_website.order", values)

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
    def order_decline(self, order_id, token=None, **post):
        order_obj = request.registry.get('service.order')
        order = order_obj.browse(request.cr, SUPERUSER_ID, order_id)
        if token != order.access_token:
            return request.website.render('website.404')
        
        message = post.get('decline_message')
        order_obj.action_rejected(request.cr, SUPERUSER_ID, [order_id])
        if message:
            order_obj.message_post(request.cr, SUPERUSER_ID, [order_id], body= message)

        return werkzeug.utils.redirect("/service/order/%s/%s?message=2" % (order_id, token))


    @http.route(['/service/order/comment/<int:order_id>',
                 '/service/order/comment/<int:order_id>/<token>'], type='http', auth="public",methods=['POST'], website=True)
    def service_comment(self, order_id, token=None, **post):
        print "trece pe aici"
        if token:
            order_obj = request.registry.get('service.order')
            order = order_obj.browse(request.cr, SUPERUSER_ID, order_id)           
            if token != order.access_token:
                return request.website.render('website.404')
            cr, uid, context = request.cr, SUPERUSER_ID, request.context
        else:
            if not request.session.uid:
                return login_redirect()
            cr, uid, context = request.cr, request.uid, request.context
            
        if post.get('comment'):
            request.registry['service.order'].message_post(
                cr, uid, order_id,
                body=post.get('comment'),
                type='comment',
                subtype='mt_comment',
                context=dict(context, mail_create_nosubscribe=True))
        if token:
            url = '/service/order/%s/%s#comments' % (order_id, token)
        else:
            url = '/service/order/%s#comments' % order_id
        return werkzeug.utils.redirect(url)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
