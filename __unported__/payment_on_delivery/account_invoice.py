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

 
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare



class account_invoice(models.Model):
    _inherit = "account.invoice"
 
    
    payment_acquirer_id = fields.Many2one('payment.acquirer', string='Payment Acquirer', on_delete='set null',
                                           copy=False, readonly=True, states={'draft': [('readonly', False)]})
 
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines =  super(account_invoice,self).finalize_invoice_move_lines(move_lines)
        # sper ca e doar o factura 
        if self.type in ('out_invoice'):
            if self.payment_acquirer_id and self.payment_acquirer_id.account_debit:
                for move in move_lines:
                    if move[2]['debit'] <> 0.0:
                        new_move = dict(move[2])
                        new_move['credit']=new_move['debit']
                        new_move['debit'] = 0.0
                        move_lines += [(0,0,new_move)]
                        
                        new_move = dict(move[2])
                        new_move['partner_id'] = self.payment_acquirer_id.partner_id.id
                        new_move['account_id'] = self.payment_acquirer_id.account_debit.id                        
                        move_lines += [(0,0,new_move)]                       
                        break
        return move_lines
        


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
