# coding=utf-8
from odoo import api, models




class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    @api.multi
    def _get_stock_move_price_unit(self):
        self.ensure_one()
        price_unit = super(PurchaseOrderLine, self.with_context(date=self.date_planned))._get_stock_move_price_unit()
        return price_unit