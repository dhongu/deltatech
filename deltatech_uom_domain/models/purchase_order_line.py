# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "deltatech.uom.domain.mixin"]

    @api.depends("product_id.purchase_uom_id")
    def _compute_allowed_uom_ids(self):
        """EXTENDS 'purchase' - ofera toate unitatile convertibile, nu doar cele legate de produs.

        Cand produsul are UM implicita de achizitie, doar ea e permisa.
        """
        res = super()._compute_allowed_uom_ids()
        with_purchase_uom = self.filtered(lambda line: line.product_id.purchase_uom_id)
        (self - with_purchase_uom)._extend_allowed_uom_ids()
        for line in with_purchase_uom:
            line.allowed_uom_ids = line.product_id.purchase_uom_id
        return res

    def _suggest_quantity(self):
        """EXTENDS 'purchase' - UM implicita de achizitie a produsului.

        In 19.0 UM de pe comanda vine doar de pe linia de furnizor valabila la data comenzii;
        `uom_po_id` de pe produs a disparut. Fara linie valabila (lipsa, expirata, alt furnizor),
        comanda pune tacut UM produsului: 4,894 mc de cherestea intra in stoc ca 4,894 buc.
        """
        res = super()._suggest_quantity()
        if self.product_id.purchase_uom_id:
            self.product_uom_id = self.product_id.purchase_uom_id
        return res
