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
from odoo.exceptions import except_orm, Warning, RedirectWarning,ValidationError
import odoo.addons.decimal_precision as dp


class account_payment_term_rate_wizard(models.TransientModel):
    _name = "account.payment.term.rate.wizard"
    _description = "Payment Term Rate Wizard"

    name = fields.Char(string="Name", required=True)
    rate = fields.Integer(string="Rate", required=True)
    advance = fields.Float(string="Advance", digits=dp.get_precision('Payment Term'), required=True)
    days2 = fields.Integer(string='Day of the Month', required=True)

    @api.one
    @api.constrains('rate')
    def _check_rate(self):
        if self.rate < 1:
            raise ValidationError("Rate must be greater than 1")

    @api.one
    @api.constrains('advance')
    def _check_advance(self):
        if self.advance < 0.0 or self.advance > 1.0:
            raise ValidationError("Percentages for Advance must be between 0 and 1, Example: 0.02 for 2%.")

    @api.multi
    def do_create_rate(self):
        line_ids = []
        first_rate = {'value': 'procent', 'value_amount': self.advance, 'days': 0, 'days2': self.days2}
        line_ids.append((0, 0, first_rate))
        if self.rate > 2:
            rest = (1 - self.advance) / (self.rate - 1)

        for x in range(1, self.rate):
            norm_rate = {'value': 'procent', 'value_amount': rest, 'days': 30 * x, 'days2': self.days2}
            line_ids.append((0, 0, norm_rate))

        line_ids[-1] = (0, 0, {'value': 'balance', 'days': 30 * (self.rate - 1), 'days2': self.days2})

        self.env["account.payment.term"].create({'name': self.name, 'line_ids': line_ids})
