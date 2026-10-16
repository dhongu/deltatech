# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_website_free_qty(self):
        """Free quantity of the shop warehouse, expressed in the unit of the line."""
        self.ensure_one()
        product = self.product_id.sudo()
        free_qty = self.order_id._get_free_qty(product)
        if self.product_uom_id and self.product_uom_id != product.uom_id:
            free_qty = product.uom_id._compute_quantity(free_qty, self.product_uom_id, round=False)
        return free_qty
