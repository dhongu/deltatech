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



class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    in_rates = fields.Boolean(string="In Rates", compute="_compute_in_rates", store=True)


    @api.multi
    @api.depends('payment_term')
    def _compute_in_rates(self):
        for invoice in self:
            in_rates = False
            if invoice.payment_term:
                if len(invoice.payment_term.line_ids) > 1:
                    in_rates = True

            invoice.in_rates = in_rates
            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
