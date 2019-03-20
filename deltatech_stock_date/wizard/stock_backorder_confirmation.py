# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'


    date = fields.Datetime(string="Date", related='pick_ids.scheduled_date')


    @api.model
    def default_get(self, fields_list):
        res = super(StockBackorderConfirmation, self).default_get(fields_list)
        return res

    @api.one
    def _process(self, cancel_backorder=False):
        self.pick_ids.write({'date': self.date})
        super(StockBackorderConfirmation, self.with_context(use_date=self.date))._process(cancel_backorder)
