# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductUomConversion(models.Model):
    """Product specific conversion between an alternative UoM and the base UoM.

    SAP MARM style: ``uom_qty`` units of ``uom_id`` = ``base_qty`` units of the
    product base UoM (e.g. 3 m² = 4 Units, 1 kg = 2 Units).
    """

    _name = "deltatech.product.uom.conversion"
    _description = "Product UoM Conversion"
    _rec_name = "uom_id"

    product_tmpl_id = fields.Many2one(
        "product.template", string="Product", required=True, index=True, ondelete="cascade"
    )
    uom_id = fields.Many2one("uom.uom", string="Alternative Unit", required=True, ondelete="restrict")
    uom_qty = fields.Float(string="Alternative Quantity", default=1.0, digits="Product Unit", required=True)
    base_uom_id = fields.Many2one(related="product_tmpl_id.uom_id", string="Base Unit")
    base_qty = fields.Float(string="Base Quantity", default=1.0, digits="Product Unit", required=True)
    factor = fields.Float(
        string="Factor",
        compute="_compute_factor",
        digits=0,
        help="How many base units correspond to one alternative unit.",
    )

    _uom_uniq = models.Constraint(
        "unique(product_tmpl_id, uom_id)",
        "A product can have only one conversion per unit of measure.",
    )

    @api.depends("uom_qty", "base_qty")
    def _compute_factor(self):
        for conv in self:
            conv.factor = conv.base_qty / conv.uom_qty if conv.uom_qty else 0.0

    @api.constrains("uom_qty", "base_qty")
    def _check_quantities(self):
        for conv in self:
            if conv.uom_qty <= 0 or conv.base_qty <= 0:
                raise ValidationError(self.env._("Conversion quantities must be strictly positive."))

    @api.constrains("uom_id", "product_tmpl_id")
    def _check_uom(self):
        for conv in self:
            if conv.uom_id == conv.product_tmpl_id.uom_id:
                raise ValidationError(self.env._("The alternative unit must be different from the product base unit."))

    def _to_base_qty(self, qty):
        """Convert a quantity expressed in ``uom_id`` into the product base UoM."""
        self.ensure_one()
        return qty * self.base_qty / self.uom_qty

    def _from_base_qty(self, qty):
        """Convert a quantity expressed in the product base UoM into ``uom_id``."""
        self.ensure_one()
        return qty * self.uom_qty / self.base_qty
