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
##############################################################################


from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta

class invoice(models.Model):
    _inherit = 'account.invoice'
    
    
    penalty = fields.Float(string='Penalty',  digits=dp.get_precision('Account'), compute='_compute_penalty' )


    @api.one
    @api.depends('payment_term','date_invoice','amount_untaxed')
    def _compute_penalty(self):
        self.penalty =  0.0
        if self.date_due:
            if self.payment_ids:
                effective_date_due = min(payment.date for payment in self.payment_ids)
            else:  
                effective_date_due = fields.Date.today()
            if self.date_due < effective_date_due:
                days = (datetime.strptime(effective_date_due, '%Y-%m-%d') - datetime.strptime(self.date_due, '%Y-%m-%d') ).days
                self.penalty = self.amount_untaxed * days * 0.01



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





