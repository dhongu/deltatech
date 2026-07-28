# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round


class ProductTemplate(models.Model):
    _inherit = "product.template"

    qty_multiple = fields.Float(
        "Qty Multiple",
        digits="Product Unit",
        default=1,
        compute="_compute_qty_multiple",
        inverse="_inverse_qty_multiple",
        store=True,
        help=("The sale quantity will be rounded up to this multiple. If it is 0 or 1, no multiple is enforced."),
    )
    qty_minim = fields.Float(
        "Qty Minim",
        digits="Product Unit",
        default=0,
        compute="_compute_qty_multiple",
        inverse="_inverse_qty_minim",
        store=True,
        help="The minimum sale quantity. If it is 0, no minimum is enforced.",
    )

    @api.depends(
        "product_variant_ids",
        "product_variant_ids.qty_multiple",
        "product_variant_ids.qty_minim",
    )
    def _compute_qty_multiple(self) -> None:
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.qty_multiple = template.product_variant_ids.qty_multiple
            template.qty_minim = template.product_variant_ids.qty_minim
        for template in self - unique_variants:
            template.qty_multiple = -1.0
            template.qty_minim = -1.0

    def _inverse_qty_multiple(self) -> None:
        for product in self:
            if len(product.product_variant_ids) == 1:
                product.product_variant_ids.qty_multiple = product.qty_multiple

    def _inverse_qty_minim(self) -> None:
        for product in self:
            if len(product.product_variant_ids) == 1:
                product.product_variant_ids.qty_minim = product.qty_minim


class ProductProduct(models.Model):
    _inherit = "product.product"

    qty_multiple = fields.Float(
        "Qty Multiple",
        digits="Product Unit",
        default=1,
        help=("The sale quantity will be rounded up to this multiple. If it is 0 or 1, no multiple is enforced."),
    )
    qty_minim = fields.Float(
        "Qty Minim",
        digits="Product Unit",
        default=0,
        help="The minimum sale quantity. If it is 0, no minimum is enforced.",
    )

    _qty_multiple_non_negative = models.Constraint(
        "CHECK(qty_multiple >= 0)",
        "The sale quantity multiple must be greater than or equal to zero.",
    )
    _qty_minim_non_negative = models.Constraint(
        "CHECK(qty_minim >= 0)",
        "The minimum sale quantity must be greater than or equal to zero.",
    )

    @api.constrains("qty_multiple", "qty_minim")
    def _check_sale_quantity_rules(self) -> None:
        if any(product.qty_multiple < 0 for product in self):
            raise ValidationError(_("The sale quantity multiple must be greater than or equal to zero."))
        if any(product.qty_minim < 0 for product in self):
            raise ValidationError(_("The minimum sale quantity must be greater than or equal to zero."))

    def _should_enforce_sale_quantity_rules(self) -> bool:
        """Return whether quantity rules apply in the current business context."""
        self.ensure_one()
        return True

    def _get_sale_quantity_rules(self, product_uom) -> tuple[float, float]:
        """Return ``(minimum, multiple)`` converted to ``product_uom``.

        Rules are configured in the product's default UoM. A configured multiple
        of 1 keeps the historical meaning of "no multiple restriction".
        """
        self.ensure_one()
        if not self._should_enforce_sale_quantity_rules():
            return 0.0, 0.0

        product_uom = product_uom or self.uom_id
        minimum = self.uom_id._compute_quantity(self.qty_minim, product_uom, round=False)
        multiple = 0.0
        if (
            self.qty_multiple
            and float_compare(
                self.qty_multiple,
                1.0,
                precision_rounding=self.uom_id.rounding,
            )
            != 0
        ):
            multiple = self.uom_id._compute_quantity(
                self.qty_multiple,
                product_uom,
                round=False,
            )
        return minimum, multiple

    def _normalize_sale_quantity(self, quantity: float, product_uom) -> float:
        """Round a positive quantity up so all configured rules are satisfied."""
        self.ensure_one()
        # This runs from create()/write() on the raw values dict, before the ORM
        # coerces the field, so the quantity may still be a string (EDI imports,
        # data loads, RPC callers). Cast it instead of raising a TypeError on the
        # comparison below.
        quantity = float(quantity or 0.0)
        if quantity <= 0:
            return quantity

        product_uom = product_uom or self.uom_id
        minimum, multiple = self._get_sale_quantity_rules(product_uom)
        if not minimum and not multiple:
            return quantity
        normalized = max(quantity, minimum)
        if multiple:
            normalized = (
                float_round(
                    normalized / multiple,
                    precision_rounding=1.0,
                    rounding_method="UP",
                )
                * multiple
            )
        return product_uom.round(normalized, rounding_method="UP")

    def _valid_sale_quantity_at_most(self, quantity: float, product_uom) -> float:
        """Return the greatest rule-compliant quantity not exceeding ``quantity``."""
        self.ensure_one()
        quantity = float(quantity or 0.0)
        if quantity <= 0:
            return 0.0

        product_uom = product_uom or self.uom_id
        minimum, multiple = self._get_sale_quantity_rules(product_uom)
        if not minimum and not multiple:
            return quantity
        if float_compare(quantity, minimum, precision_rounding=product_uom.rounding) < 0:
            return 0.0

        valid_quantity = quantity
        if multiple:
            valid_quantity = (
                float_round(
                    quantity / multiple,
                    precision_rounding=1.0,
                    rounding_method="DOWN",
                )
                * multiple
            )
        valid_quantity = product_uom.round(valid_quantity, rounding_method="DOWN")
        if (
            float_compare(
                valid_quantity,
                minimum,
                precision_rounding=product_uom.rounding,
            )
            < 0
        ):
            return 0.0
        return valid_quantity
