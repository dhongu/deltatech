from odoo import models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _prepare_base_line_for_taxes_computation(self):
        res = super()._prepare_base_line_for_taxes_computation()

        fiscal_position = self.order_id.fiscal_position_id
        if fiscal_position:
            # În JS este: const original_taxes = this.tax_ids || product.taxes_id;
            # Aici line.tax_ids sunt taxele de pe linie (originale din POS înainte de mapare)
            original_taxes = self.tax_ids
            new_taxes = res.get("tax_ids")

            # Dacă taxele s-au schimbat prin poziția fiscală, trebuie să adaptăm prețul unitar
            # Odoo core folosește prețul unitar direct, ceea ce e greșit dacă taxele incluse s-au schimbat
            if set(original_taxes.ids) != set(new_taxes.ids):
                res["price_unit"] = self.env["account.tax"]._adapt_price_unit_to_another_taxes(
                    self.price_unit,
                    self.product_id,
                    original_taxes,
                    new_taxes,
                    product_uom=self.product_uom_id,
                )

        return res
