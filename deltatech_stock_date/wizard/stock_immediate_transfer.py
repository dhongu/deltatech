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


    date = fields.Datetime(string="Date", related='pick_ids.scheduled_date',  store=False, readonly=False)

    @api.model
    def default_get(self, fields_list):
        res = super(StockImmediateTransfer, self).default_get(fields_list)
        return res

    @api.multi
    def process(self):
        self.pick_ids.write({'date':self.date})
        return super(StockImmediateTransfer, self.with_context(use_date=self.date)).process()


