# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Deltatech All Rights Reserved
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




class AccountVoucher(models.Model):
    _inherit = 'account.voucher'


    @api.model
    def _get_journal(self):
        res = super(AccountVoucher, self)._get_journal()
        invoice_id = self.env.context.get('invoice_id', False)
        if invoice_id:
            invoice = self.env['account.invoice'].browse(invoice_id)
            if invoice.type == 'out_invoice' and invoice.journal_id.fiscal_receipt:
                journal = self.env['account.invoice'].search([
                    ('company_id', '=', invoice.company_id.id),
                    ('type','=','cash'),
                    ('fiscal_receipt','=',True)
                ])
                if journal:
                    return journal.id

        return res
