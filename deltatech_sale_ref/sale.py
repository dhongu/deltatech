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



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from openerp.osv.fields import related
 
_logger = logging.getLogger(__name__)

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_order_line_procurement(self,  order, line, group_id=False ):
        res = super(sale_order,self)._prepare_order_line_procurement(order, line, group_id)
        if line.delivery_date:
            res['date_planned'] = line.delivery_date
        return res

    @api.model
    def _get_date_planned(self,   order, line, start_date):
        res = super(sale_order,self)._get_date_planned(order, line, start_date)
        if line.delivery_date:
            res = line.delivery_date
        return res


    @api.multi
    def action_button_confirm(self):
        res = super(sale_order,self).action_button_confirm()
        return res
               
class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    ref = fields.Char(string="Reference")
    delivery_date = fields.Date(string="Delivery Date") 
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: