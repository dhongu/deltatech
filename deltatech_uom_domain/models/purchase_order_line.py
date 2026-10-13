# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "deltatech.uom.domain.mixin"]

    def _compute_allowed_uom_ids(self):
        """EXTENDS 'purchase' - ofera toate unitatile convertibile, nu doar cele legate de produs."""
        res = super()._compute_allowed_uom_ids()
        self._extend_allowed_uom_ids()
        return res
