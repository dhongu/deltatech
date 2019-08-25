# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

 

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

