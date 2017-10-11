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
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp

class account_cash_update_balances(models.TransientModel):
    _name = 'account.cash.update.balances'
    _description = "Account Cash Update Balances"


    balance_start = fields.Float(string='Starting Balance', digits=dp.get_precision('Account'))

    @api.model
    def default_get(self, fields): 
        defaults = super(account_cash_update_balances, self).default_get(fields)         
        active_ids = self.env.context.get('active_ids', False)
        statement = False
        if active_ids:
            statement = self.env['account.bank.statement'].search([('id','in',active_ids),('state','=','open')],order='date',limit=1)
            if statement:
                defaults['balance_start'] = statement.balance_start
        if not statement:
            raise Warning(_('Please select cash statement'))
        return defaults
    
    
    @api.multi
    def do_update_balance(self):
        active_ids = self.env.context.get('active_ids', False)
        statement = False
        if active_ids:
            statements = self.env['account.bank.statement'].search([('id','in',active_ids),('state','=','open')],order='date')
            balance_start = self.balance_start
            for statement in statements:
                statement.write({'balance_start':balance_start})
                statement.write({'balance_end_real':statement.balance_end})
                balance_start = statement.balance_end
            


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
