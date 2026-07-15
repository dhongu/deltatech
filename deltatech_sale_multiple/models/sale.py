# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from typing import Any

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def fix_qty_multiple(self, product, product_uom, qty: float | None = None) -> float:
        """Compatibility wrapper for callers of the historical public helper."""
        if not product:
            return qty or 0.0
        return product._normalize_sale_quantity(qty or 0.0, product_uom)

    @api.onchange("product_uom_qty", "product_id", "product_uom_id")
    def _onchange_product_uom_qty(self) -> None:
        if not self.product_id:
            return
        product_uom = self.product_uom_id or self.product_id.uom_id
        self.product_uom_qty = self.fix_qty_multiple(
            self.product_id,
            product_uom,
            self.product_uom_qty,
        )

    @api.model
    def _prepare_quantity_rule_values(
        self,
        vals: dict[str, Any],
        line=None,
    ) -> dict[str, Any]:
        values = dict(vals)
        product = (
            self.env["product.product"].browse(values["product_id"])
            if values.get("product_id")
            else line.product_id
            if line
            else self.env["product.product"]
        )
        if not product or values.get("display_type"):
            return values

        product_uom = (
            self.env["uom.uom"].browse(values["product_uom_id"])
            if values.get("product_uom_id")
            else line.product_uom_id
            if line
            else product.uom_id
        )
        if "product_uom_qty" in values:
            quantity = values["product_uom_qty"]
        elif line and "product_uom_id" in values:
            quantity = line.product_uom_id._compute_quantity(
                line.product_uom_qty,
                product_uom,
                round=False,
            )
        else:
            quantity = line.product_uom_qty if line else 1.0
        values["product_uom_qty"] = self.fix_qty_multiple(
            product,
            product_uom,
            quantity,
        )
        return values

    @api.model_create_multi
    def create(self, vals_list: list[dict[str, Any]]):
        normalized_vals = [self._prepare_quantity_rule_values(vals) for vals in vals_list]
        return super().create(normalized_vals)

    def write(self, vals: dict[str, Any]) -> bool:
        rule_fields = {"product_id", "product_uom_id", "product_uom_qty"}
        if not rule_fields.intersection(vals):
            return super().write(vals)

        for line in self:
            line_vals = self._prepare_quantity_rule_values(vals, line=line)
            super(SaleOrderLine, line).write(line_vals)
        return True
