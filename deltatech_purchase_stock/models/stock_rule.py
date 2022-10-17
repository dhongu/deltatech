# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_purchase_order(self, product_id, product_qty, product_uom, origin, values, partner):
        values = super(StockRule, self)._prepare_purchase_order(
            product_id, product_qty, product_uom, origin, values, partner
        )
        values["from_replenishment"] = True
        return values

    def _make_po_get_domain(self, values, partner):
        domain = super(StockRule, self)._make_po_get_domain(values, partner)
        domain += (("from_replenishment", "=", True),)
        return domain
