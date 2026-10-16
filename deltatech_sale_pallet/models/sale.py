# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

import math

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Nume propriu (nu `onchange_order_line`): alte module (ex.
    # deltatech_sale_add_extra_line) definesc `onchange_order_line` fără super(),
    # iar Odoo înregistrează un singur onchange per nume de metodă.
    @api.onchange("order_line")
    def _onchange_order_line_pallet(self):
        pallets = self.recompute_pallet_lines(delete_if_under=True)
        for line in self.order_line:
            pallet = pallets.pop(line.product_id.id, False)
            if pallet:
                # line.product_uom_qty = max(pallet["product_uom_qty"], line.product_uom_qty)
                line.product_uom_qty = pallet["product_uom_qty"]
            elif line.is_pallet_line and line.product_id.id not in pallets:
                # linie de palet generată, al cărei produs principal nu mai e pe comandă
                self._drop_obsolete_pallet_line(line)

        for product_id in pallets:
            if pallets and pallets[product_id]["product_uom_qty"]:
                order_line = self.order_line.new(dict(pallets[product_id], is_pallet_line=True))
                # `_onchange_product_id_warning` nu există în O19 nativ; e adus
                # doar de deltatech_sale_margin. Apelăm doar dacă e disponibil.
                if hasattr(order_line, "_onchange_product_id_warning"):
                    order_line._onchange_product_id_warning()
                # order_line.product_uom_change()

    def _drop_obsolete_pallet_line(self, line):
        """Elimină o linie de palet generată care nu mai are produs principal.

        Liniile salvate ale unei comenzi confirmate nu pot fi șterse: li se pune
        cantitatea 0. Liniile de palet adăugate manual (fără `is_pallet_line`) nu
        sunt atinse.
        """
        if self.state == "sale" and line._origin.id:
            line.product_uom_qty = 0.0
        else:
            self.order_line -= line

    def recompute_pallet_lines(self, delete_if_under=False):
        pallets = {}
        for line in self.order_line:
            if line.product_id.pallet_product_id and line.product_id.pallet_qty_min:
                # search for lines with same pallet
                product = line.product_id.pallet_product_id
                prod_with_pallet_lines = self.order_line.filtered(
                    lambda p, product_id=product.id: p.product_id.pallet_product_id.id == product_id
                )

                # compute sum for all lines with pallets
                qty = 0
                for prod_with_pallet_line in prod_with_pallet_lines:
                    qty += prod_with_pallet_line.compute_pallet_number(delete_if_under)

                pallets[line.product_id.pallet_product_id.id] = {
                    "product_uom_qty": qty,
                    "product_id": line.product_id.pallet_product_id.id,
                    "state": "draft",
                    "order_id": self.id,
                }
        return pallets


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_pallet_line = fields.Boolean(
        string="Generated Pallet Line",
        copy=True,
        help="Line added automatically for the pallets required by the other lines.",
    )

    def compute_pallet_number(self, delete_if_under=False):
        self.ensure_one()
        res = 0
        if self.product_id.pallet_product_id and self.product_id.pallet_qty_min:
            if self.product_id.pallet_qty_min > self.product_uom_qty:
                if delete_if_under:
                    res = 0
                else:
                    res = 1
            else:
                pallets = self.product_uom_qty / self.product_id.pallet_qty_min
                # toleranța = jumătate din precizia cantității, raportată la un palet,
                # ca erorile de virgulă mobilă să nu schimbe numărul de paleți
                digits = self.env["decimal.precision"].precision_get("Product Unit")
                epsilon = 0.5 * 10**-digits / self.product_id.pallet_qty_min
                if delete_if_under:
                    res = math.floor(pallets + epsilon)  # round down
                else:
                    res = math.ceil(pallets - epsilon)  # round up
        return res
