# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools import float_compare, float_is_zero


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    qty_multiple = fields.Float(
        string="Multiple Quantity",
        digits="Product Unit of Measure",
        default=0,
        help="The procurement quantity will be rounded to a multiple of this field "
        "quantity: down when a maximum quantity is set (so the order stays within "
        "it), up otherwise. It is never rounded down to zero - a rule that needs "
        "less than one multiple orders one full multiple instead of nothing. If it "
        "is 0, the native 'Replenishment UoM' mechanism applies instead (if set), "
        "or no rounding is applied.",
    )

    _qty_multiple_non_negative = models.Constraint(
        "CHECK(qty_multiple >= 0)",
        "Multiple Quantity must be greater than or equal to zero.",
    )

    def _get_multiple_rounded_qty(self, qty_to_order):
        """EXTENDS 'stock' - restaura rotunjirea prin `qty_multiple`.

        Odoo a eliminat acest camp in 19.0, inlocuindu-l cu `replenishment_uom_id`
        (o unitate de masura ce trebuie legata explicit de produs/furnizor). Daca
        `qty_multiple` e setat pe orderpoint, aplicam rotunjirea directa - ca in
        Odoo <= 18.0 - fara sa fie nevoie de nicio unitate de masura suplimentara.
        Altfel, se pastreaza mecanismul nativ (`super()`).

        Fata de Odoo 18.0 exista o singura abatere, deliberata: cand exista un
        plafon (`product_max_qty`), rotunjirea se face in jos ca sa nu-l depaseasca,
        dar nu pana la 0. Daca necesarul e mai mic decat multiplul, rotunjirea nativa
        il duce la zero si regula nu mai comanda *niciodata* - un plafon sub multiplu
        dezactiveaza regula in tacere. In cazul asta comandam un multiplu intreg;
        depasirea plafonului e preferabila unei reguli moarte.
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
            capped = not float_is_zero(self.product_max_qty, precision_rounding=rounding)
            if capped and float_compare(qty_to_order - remainder, 0.0, precision_rounding=rounding) > 0:
                qty_to_order -= remainder
            else:
                qty_to_order += self.qty_multiple - remainder
        return qty_to_order
