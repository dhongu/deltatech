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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, RedirectWarning


class account_move_line(models.Model):
    _inherit = "account.move.line"

    payment_date = fields.Date(string="Payment Date", compute="_compute_payment_days", store=True)
    payment_days = fields.Integer(string="Payment Days", compute="_compute_payment_days", store=True)

    @api.depends('date', 'reconcile_id')
    @api.multi
    def _compute_payment_days(self):
        for aml in self:
            if aml.reconcile_id and aml.journal_id.type in ['sale', 'purchase', 'sale_refund', 'purchase_refund']:
                payment_date = fields.Date.context_today(self)
                if aml.debit > 0:
                    for line in aml.reconcile_id.line_id:
                        if line.credit > 0:
                            payment_date = line.date
                            break
                if aml.credit > 0:
                    for line in aml.reconcile_id.line_id:
                        if line.debit > 0:
                            payment_date = line.date
                            break
                aml.payment_date = payment_date
            if aml.payment_date:
                diff = fields.Date.from_string(aml.payment_date) - fields.Date.from_string(aml.date)
                aml.payment_days = diff.days
