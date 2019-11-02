# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    date_done = fields.Datetime(string="Date")

    @api.model
    def default_get(self, fields_list):
        res = super(StockImmediateTransfer, self).default_get(fields_list)
        res['date_done'] = self.env.context.get('force_period_date',fields.Datetime.now())
        return res

    @api.multi
    def process(self):
        self.pick_ids.write({'date': self.date_done, 'date_done': self.date_done})
        return super(StockImmediateTransfer, self.with_context(force_period_date=self.date_done)).process()
