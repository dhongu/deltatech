# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "deltatech.uom.domain.mixin"]

    def _compute_allowed_uom_ids(self):
        """EXTENDS 'purchase' - ofera toate unitatile convertibile, nu doar cele legate de produs."""
        res = super()._compute_allowed_uom_ids()
        self._extend_allowed_uom_ids()
        return res

    def _suggest_quantity(self):
        """EXTENDS 'purchase' - UM implicita de achizitie a produsului, cand furnizorul n-are linie valabila.

        In 19.0 UM de pe comanda vine doar de pe linia de furnizor valabila la data comenzii;
        `uom_po_id` de pe produs a disparut. Fara linie valabila (lipsa, expirata, alt furnizor),
        comanda pune tacut UM produsului: 4,894 mc de cherestea intra in stoc ca 4,894 buc.
        """
        res = super()._suggest_quantity()
        purchase_uom = self.product_id.purchase_uom_id
        if purchase_uom and not self._get_valid_sellers_for_suggest():
            self.product_uom_id = purchase_uom
        return res

    def _get_valid_sellers_for_suggest(self):
        """Acelasi filtru ca in `_suggest_quantity` din 'purchase'."""
        self.ensure_one()
        date = self.order_id.date_order and self.order_id.date_order.date() or fields.Date.context_today(self)
        return self.product_id.seller_ids.filtered(
            lambda r: r.partner_id == self.order_id.partner_id
            and (not r.product_id or r.product_id == self.product_id)
            and (not r.date_start or r.date_start <= date)
            and (not r.date_end or r.date_end >= date)
        )
