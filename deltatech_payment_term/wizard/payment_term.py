# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
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
        if self.advance < 0.0 or self.advance > 100.0:
            raise ValidationError("Percentages for Advance must be between 0 and 100.")

    @api.multi
    def do_create_rate(self):
        line_ids = []
        first_rate = {'value': 'percent', 'value_amount': self.advance, 'days': 0, 'days2': self.days2}
        line_ids.append((0, 0, first_rate))
        if self.rate > 2:
            rest = (1 - self.advance/100) / (self.rate - 1)

        for x in range(1, self.rate):
            norm_rate = {'value': 'percent', 'value_amount': rest*100, 'days': 30 * x, 'days2': self.days2}
            line_ids.append((0, 0, norm_rate))

        line_ids[-1] = (0, 0, {'value': 'balance', 'days': 30 * (self.rate - 1), 'days2': self.days2})

        self.env["account.payment.term"].create({'name': self.name, 'line_ids': line_ids})
