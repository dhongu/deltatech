from typing import Any

from odoo import api, models
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _verify_updated_quantity(
        self,
        order_line,
        product_id,
        new_qty,
        uom_id,
        **kwargs,
    ) -> tuple[float, str]:
        """Apply quantity rules before stock and other cart verifications.

        A downstream verifier may cap the requested quantity (for example to
        available stock). In that case, cap it again to the greatest quantity
        that still satisfies the product rules.
        """
        product = (
            self.env["product.product"]
            .browse(product_id)
            .with_context(website_id=self.website_id.id or self.env.context.get("website_id"))
        )
        product_uom = self.env["uom.uom"].browse(uom_id) or product.uom_id
        normalized_qty = product._normalize_sale_quantity(new_qty, product_uom)
        verified_qty, warning = super()._verify_updated_quantity(
            order_line,
            product_id,
            normalized_qty,
            uom_id,
            **kwargs,
        )
        if (
            verified_qty > 0
            and float_compare(
                verified_qty,
                normalized_qty,
                precision_rounding=product_uom.rounding,
            )
            < 0
        ):
            verified_qty = product._valid_sale_quantity_at_most(
                verified_qty,
                product_uom,
            )
        return verified_qty, warning


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def _prepare_quantity_rule_values(
        self,
        vals: dict[str, Any],
        line=None,
    ) -> dict[str, Any]:
        order = (
            self.env["sale.order"].browse(vals["order_id"])
            if vals.get("order_id")
            else line.order_id
            if line
            else self.env["sale.order"]
        )
        if not order.website_id:
            return super()._prepare_quantity_rule_values(vals, line=line)

        website_context = {"website_id": order.website_id.id}
        contextual_self = self.with_context(**website_context)
        contextual_line = line.with_context(**website_context) if line else line
        return super(SaleOrderLine, contextual_self)._prepare_quantity_rule_values(
            vals,
            line=contextual_line,
        )
