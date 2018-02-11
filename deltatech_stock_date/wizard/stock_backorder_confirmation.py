# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    date = fields.Datetime(string="Date", related='pick_id.min_date')

    @api.one
    def _process(self, cancel_backorder=False):

        super(StockBackorderConfirmation, self.with_context(use_date=self.date))._process(cancel_backorder)

