# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _



class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    
    date = fields.Datetime(string="Date", related='pick_id.min_date')


    @api.multi
    def process(self):
        return super(StockImmediateTransfer, self.with_context(use_date=self.date)).process()


