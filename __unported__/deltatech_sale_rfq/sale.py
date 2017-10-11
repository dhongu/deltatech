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



from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from odoo.osv.fields import related
 
_logger = logging.getLogger(__name__)



class sale_order(models.Model):
    _inherit = 'sale.order'
    
    @api.multi
    def action_quotation_is_ready(self):
        rfq_ids = self.env['sale.rfq'].search([('order_id','=',self.id)])
        if not rfq_ids:
            raise Warning(_('RFQ not found'))
        rfq_ids.quotation_ready()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: