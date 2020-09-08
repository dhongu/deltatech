# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def recompute_residual(self):
        invoices = self.search([('amount_untaxed', '<', '0')])
        invoices._compute_residual()

    def _compute_residual(self):
        for invoice in self:
            super(account_invoice, invoice)._compute_residual()
            if invoice.amount_total_signed < 0.0:
                if invoice.residual_signed > 0.0:
                    invoice.residual_signed = -1 * invoice.residual_signed
                if invoice.residual > 0.0 and invoice.type not in ['in_refund', 'out_refund']:
                    invoice.residual = -1 * invoice.residual
