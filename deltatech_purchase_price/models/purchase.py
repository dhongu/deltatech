# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _add_supplier_to_product(self):
        #todo: de adaugat parametru in configurare
        add_supplier_to_product = self.env['ir.config_parameter'].sudo().get_param('purchase.add_supplier_to_product')
        if add_supplier_to_product == 'False':
            add_supplier_to_product = False
        if add_supplier_to_product:
            super(PurchaseOrder, self)._add_supplier_to_product()

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _get_stock_move_price_unit(self):
        self.ensure_one()
        price_unit = super(PurchaseOrderLine, self.with_context(date=self.date_planned))._get_stock_move_price_unit()
        return price_unit
