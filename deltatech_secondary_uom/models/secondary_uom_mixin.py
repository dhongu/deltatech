# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools import float_round


class SecondaryUomMixin(models.AbstractModel):
    """Adds a secondary quantity/UoM pair on document lines.

    The secondary quantity is linked to the line quantity through the product
    specific conversions (deltatech.product.uom.conversion). Editing either
    side updates the other. Concrete models must implement the hook methods
    below and redeclare the compute with the proper @api.depends.
    """

    _name = "deltatech.secondary.uom.mixin"
    _description = "Secondary UoM Mixin"

    secondary_uom_id = fields.Many2one(
        "uom.uom",
        string="Secondary Unit",
        domain="[('id', 'in', allowed_secondary_uom_ids)]",
        ondelete="restrict",
    )
    secondary_uom_qty = fields.Float(
        string="Secondary Quantity",
        digits="Product Unit",
        compute="_compute_secondary_uom_qty",
        inverse="_inverse_secondary_uom_qty",
        store=True,
        readonly=False,
    )
    allowed_secondary_uom_ids = fields.Many2many(
        "uom.uom", compute="_compute_allowed_secondary_uom_ids", string="Allowed Secondary Units"
    )

    # hooks: concrete models must implement these
    def _get_secondary_product(self):
        """Return the product.product of the line."""
        raise NotImplementedError

    def _get_line_qty_and_uom(self):
        """Return (quantity, uom) of the line, in the line UoM."""
        raise NotImplementedError

    def _set_line_qty(self, qty):
        """Write the given quantity (expressed in the line UoM) on the line."""
        raise NotImplementedError

    def _get_secondary_uom_open_domain(self):
        """Domain of the lines still editable, recomputed when a conversion changes."""
        return []

    def _get_secondary_conversion(self):
        self.ensure_one()
        product = self._get_secondary_product()
        if not product or not self.secondary_uom_id:
            return self.env["deltatech.product.uom.conversion"]
        return product.product_tmpl_id._get_secondary_uom_conversion(self.secondary_uom_id)

    def _compute_allowed_secondary_uom_ids(self):
        for line in self:
            product = line._get_secondary_product()
            line.allowed_secondary_uom_ids = product.product_tmpl_id.secondary_uom_ids.uom_id if product else False

    def _compute_secondary_uom_qty(self):
        for line in self:
            conv = line._get_secondary_conversion()
            if not conv:
                line.secondary_uom_qty = 0.0
                continue
            product = line._get_secondary_product()
            qty, uom = line._get_line_qty_and_uom()
            qty_base = uom._compute_quantity(qty, product.uom_id, round=False) if uom else qty
            line.secondary_uom_qty = conv._from_base_qty(qty_base)

    def _is_piece_uom(self, uom):
        """Whether ``uom`` counts pieces (same reference tree as the standard Unit)."""
        unit = self.env.ref("uom.product_uom_unit", raise_if_not_found=False)
        return bool(uom and unit and uom._has_common_reference(unit))

    def _round_secondary_base_qty(self, product, qty_base):
        """Round a base quantity computed from the secondary quantity."""
        if self._is_piece_uom(product.uom_id):
            # round up to whole pieces: we cannot deliver fractional pieces
            return float_round(qty_base, precision_rounding=1.0, rounding_method="UP")
        # continuous unit (m, kg, m²): keep the exact quantity
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        return float_round(qty_base, precision_digits=digits, rounding_method="HALF-UP")

    @api.model
    def _complete_secondary_create_vals(self, vals_list, qty_field, uom_field):
        """Fill the line quantity from the secondary quantity before ``create``.

        When a line is created with the secondary quantity but without its own
        quantity (API, import), the inverse would set the quantity only after
        the precomputed fields (amounts, taxes) were computed with the default
        quantity, and ``create`` protects them from recomputation.
        """
        Uom = self.env["uom.uom"]
        for vals in vals_list:
            if qty_field in vals or not vals.get("secondary_uom_qty"):
                continue
            if not vals.get("secondary_uom_id") or not vals.get("product_id"):
                continue
            product = self.env["product.product"].browse(vals["product_id"])
            conv = product.product_tmpl_id._get_secondary_uom_conversion(Uom.browse(vals["secondary_uom_id"]))
            if not conv:
                continue
            qty_base = self._round_secondary_base_qty(product, conv._to_base_qty(vals["secondary_uom_qty"]))
            uom = Uom.browse(vals[uom_field]) if vals.get(uom_field) else product.uom_id
            vals[qty_field] = product.uom_id._compute_quantity(qty_base, uom, rounding_method="HALF-UP")
        return vals_list

    def _inverse_secondary_uom_qty(self):
        for line in self:
            conv = line._get_secondary_conversion()
            if not conv:
                continue
            product = line._get_secondary_product()
            qty_base = line._round_secondary_base_qty(product, conv._to_base_qty(line.secondary_uom_qty))
            qty_line = qty_base
            qty, uom = line._get_line_qty_and_uom()
            if uom:
                qty_line = product.uom_id._compute_quantity(qty_base, uom, rounding_method="HALF-UP")
            line._set_line_qty(qty_line)
            # realign the secondary quantity with the rounded piece count
            # (the compute is protected against retriggering during the inverse)
            line.secondary_uom_qty = conv._from_base_qty(qty_base)
