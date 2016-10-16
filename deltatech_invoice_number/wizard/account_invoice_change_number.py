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

 

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp

class account_invoice_change_number(models.TransientModel):
    _name = 'account.invoice.change.number'
    _description = "Account Invoice Change Number"

    internal_number = fields.Char(string='Invoice Number')

    @api.model
    def default_get(self, fields): 
        defaults = super(account_invoice_change_number, self).default_get(fields)         
        active_id = self.env.context.get('active_id', False)
        if active_id:
            invoice = self.env['account.invoice'].browse(active_id)
            defaults['internal_number'] = invoice.internal_number
        return defaults
    
    
    @api.multi
    def do_change_number(self):
        active_id = self.env.context.get('active_id', False)
        if active_id:
            invoice = self.env['account.invoice'].browse(active_id)
            invoice.write({'number':self.internal_number,
                           'internal_number':self.internal_number })
            if invoice.state == 'open':
                invoice.action_number()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
