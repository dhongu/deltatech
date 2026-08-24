# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools import float_compare, float_is_zero


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    qty_multiple = fields.Float(
        string="Multiple Quantity",
        digits="Product Unit of Measure",
        default=1,
        help="The procurement quantity will be rounded up to a multiple of this "
        "field quantity. If it is 0, it is not rounded.",
    )

    _qty_multiple_non_negative = models.Constraint(
        "CHECK(qty_multiple >= 0)",
        "Multiple Quantity must be greater than or equal to zero.",
    )

    def _get_multiple_rounded_qty(self, qty_to_order):
        """EXTENDS 'stock' - restaura rotunjirea prin `qty_multiple`.

        Odoo a eliminat acest camp in 19.0, inlocuindu-l cu `replenishment_uom_id`
        (o unitate de masura ce trebuie legata explicit de produs/furnizor). Daca
        `qty_multiple` e setat pe orderpoint, aplicam rotunjirea directa - identica
        cu comportamentul din Odoo <= 18.0 - fara sa fie nevoie de nicio unitate de
        masura suplimentara. Altfel, se pastreaza mecanismul nativ (`super()`).
        """
        self.ensure_one()
        rounding = self.product_uom.rounding
        if float_compare(self.qty_multiple, 0.0, precision_rounding=rounding) <= 0:
            return super()._get_multiple_rounded_qty(qty_to_order)

        remainder = qty_to_order % self.qty_multiple
        if (
            float_compare(remainder, 0.0, precision_rounding=rounding) > 0
            and float_compare(self.qty_multiple - remainder, 0.0, precision_rounding=rounding) > 0
        ):
            if float_is_zero(self.product_max_qty, precision_rounding=rounding):
                qty_to_order += self.qty_multiple - remainder
            else:
                qty_to_order -= remainder
        return qty_to_order
