# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
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

    def _inverse_secondary_uom_qty(self):
        for line in self:
            conv = line._get_secondary_conversion()
            if not conv:
                continue
            product = line._get_secondary_product()
            qty_base = conv._to_base_qty(line.secondary_uom_qty)
            # round up to whole base units: we cannot deliver fractional pieces
            qty_base = float_round(qty_base, precision_rounding=1.0, rounding_method="UP")
            qty_line = qty_base
            qty, uom = line._get_line_qty_and_uom()
            if uom:
                qty_line = product.uom_id._compute_quantity(qty_base, uom, rounding_method="HALF-UP")
            line._set_line_qty(qty_line)
            # realign the secondary quantity with the rounded piece count
            # (the compute is protected against retriggering during the inverse)
            line.secondary_uom_qty = conv._from_base_qty(qty_base)
