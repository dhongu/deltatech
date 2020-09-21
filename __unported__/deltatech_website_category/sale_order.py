# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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
##############################################################################



from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp
from odoo.addons.web.http import request


class website(models.Model):
    _inherit = 'website' 


    def sale_get_order(self, cr, uid, ids, force_create=False, code=None, update_pricelist=None, context=None):
        sale_order_obj = self.pool['sale.order']
        sale_order_id = request.session.get('sale_order_id')
        if isinstance(sale_order_id, list):
            sale_order_id = sale_order_id[0]
            request.session['sale_order_id'] = sale_order_id
                    
        if not sale_order_id:
            
            user =  self.pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context)
            partner = user.partner_id
                     
            if user.active and partner: # trebuie sa fie un user activ nu userul pubic
                domain = [('partner_id','=',partner.id), ('state','=','draft')]               
                sale_order_id = sale_order_obj.search(cr, SUPERUSER_ID, domain, limit=1, context=context)
                
                if sale_order_id and isinstance(sale_order_id, list):
                    sale_order_id = sale_order_id[0]
                     
                if sale_order_id:
                    request.session['sale_order_id'] = sale_order_id
            
            
        res = super(website,self).sale_get_order(cr, uid, ids, force_create, code, update_pricelist, context)
        return res



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
