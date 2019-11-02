# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'


    date_done = fields.Datetime(string="Date")



    @api.model
    def default_get(self, fields_list):
        res = super(StockBackorderConfirmation, self).default_get(fields_list)
        res['date_done'] = self.env.context.get('force_period_date', fields.Datetime.now())
        return res



    @api.one
    def _process(self, cancel_backorder=False):
        self.pick_ids.write({'date': self.date_done})
        super(StockBackorderConfirmation, self.with_context(force_period_date=self.date_done))._process(cancel_backorder)
