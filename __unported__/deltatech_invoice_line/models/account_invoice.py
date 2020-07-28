# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _

from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
import time
from datetime import datetime


class account_invoice(models.Model):
    _inherit = "account.invoice"

    def button_invoice_show_lines(self):
        action = self.env.ref('deltatech_invoice_line.action_invoice_line').read()[0]
        action['domain'] = [('invoice_id', '=', self.id)]
        action['context'] = {'active_id': self.id, 'active_model': self._name}
        return action


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    checked = fields.Selection([('ok', 'OK'), ('not_ok', 'NOT OK'), ], string='Checked' )

    @api.multi
    def set_checked(self, value):
        self.write({'checked': value})


    @api.multi
    def compute_taxes(self):
        invoices = self.env['account.invoice']
        for line in self:
            invoices |= line.invoice_id

        invoices.compute_taxes()