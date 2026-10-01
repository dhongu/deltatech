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

    @api.model_create_multi
    def create(self, vals_list):
        convs = super().create(vals_list)
        convs._recompute_open_secondary_uom_qty(convs._get_secondary_uom_keys())
        return convs

    def write(self, vals):
        if not {"product_tmpl_id", "uom_id", "uom_qty", "base_qty"} & set(vals):
            return super().write(vals)
        # the lines of the old (product, unit) pair lose this conversion
        keys = self._get_secondary_uom_keys()
        res = super().write(vals)
        self._recompute_open_secondary_uom_qty(keys | self._get_secondary_uom_keys())
        return res

    def unlink(self):
        keys = self._get_secondary_uom_keys()
        res = super().unlink()
        self.env["deltatech.product.uom.conversion"]._recompute_open_secondary_uom_qty(keys)
        return res

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

    def _get_secondary_uom_keys(self):
        return {(conv.product_tmpl_id.id, conv.uom_id.id) for conv in self}

    @api.model
    def _recompute_open_secondary_uom_qty(self, keys):
        """Recompute the stored secondary quantity of the open document lines
        using the given (product template id, uom id) pairs.

        The ratio is live while a document can still be edited (the inverse
        uses the current ratio, so both directions must agree); closed documents
        (locked or cancelled orders, done or cancelled moves) keep the
        quantity computed with the ratio valid at that time.
        """
        if not keys:
            return
        tmpl_ids = list({key[0] for key in keys})
        uom_ids = list({key[1] for key in keys})
        for model_name in self.env.registry.descendants(["deltatech.secondary.uom.mixin"], "_inherit"):
            Line = self.env[model_name].sudo().with_context(active_test=False)
            if Line._abstract:
                continue
            domain = Line._get_secondary_uom_open_domain() + [
                ("product_id.product_tmpl_id", "in", tmpl_ids),
                ("secondary_uom_id", "in", uom_ids),
            ]
            lines = Line.search(domain).filtered(
                lambda line: (line.product_id.product_tmpl_id.id, line.secondary_uom_id.id) in keys
            )
            if lines:
                self.env.add_to_compute(Line._fields["secondary_uom_qty"], lines)

    def _to_base_qty(self, qty):
        """Convert a quantity expressed in ``uom_id`` into the product base UoM."""
        self.ensure_one()
        return qty * self.base_qty / self.uom_qty

    def _from_base_qty(self, qty):
        """Convert a quantity expressed in the product base UoM into ``uom_id``."""
        self.ensure_one()
        return qty * self.uom_qty / self.base_qty
