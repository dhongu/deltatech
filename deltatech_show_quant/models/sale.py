# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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


class sale_order(models.Model):
    _inherit = 'sale.order' 
    
     
    @api.multi
    def view_current_stock(self):
        action = self.env.ref('stock.product_open_quants').read()[0]  
        product_ids = []
        for order in self:
            product_ids += [line.product_id.id for line in order.order_line]
        action['context'] = {'search_default_internal_loc': 1, 
                             'search_default_locationgroup':1}
        
        action['domain'] = "[('product_id','in',[" + ','.join(map(str, product_ids)) + "])]"            
        return action 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
