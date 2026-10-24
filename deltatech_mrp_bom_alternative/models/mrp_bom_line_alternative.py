from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MrpBomLineAlternative(models.Model):
    _name = "mrp.bom.line.alternative"
    _description = "BoM Line Alternative Component"
    _order = "bom_line_id, sequence, id"
    _check_company_auto = True

    bom_line_id = fields.Many2one(
        "mrp.bom.line", string="BoM Line", required=True, ondelete="cascade", index=True, check_company=True
    )
    bom_id = fields.Many2one(related="bom_line_id.bom_id", store=True, index=True)
    company_id = fields.Many2one(related="bom_line_id.company_id", store=True)
    original_product_id = fields.Many2one(related="bom_line_id.product_id", string="Original Component")
    original_qty = fields.Float(related="bom_line_id.product_qty", string="Original Quantity")
    original_uom_id = fields.Many2one(related="bom_line_id.uom_id", string="Original Unit")
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        "product.product",
        string="Alternative Component",
        required=True,
        check_company=True,
        domain="[('type', '=', 'consu')]",
    )
    product_qty = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
        digits="Product Unit",
        help="Quantity of the alternative that replaces the quantity of the original component on the BoM line.",
    )
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="Unit",
        required=True,
        compute="_compute_product_uom_id",
        store=True,
        readonly=False,
        precompute=True,
    )
    date_start = fields.Date(string="Valid From")
    date_end = fields.Date(string="Valid Until")
    note = fields.Char()

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        for alternative in self:
            alternative.product_uom_id = alternative.product_id.uom_id

    @api.constrains("product_id", "bom_line_id")
    def _check_product(self):
        for alternative in self:
            if alternative.product_id == alternative.bom_line_id.product_id:
                raise ValidationError(self.env._("A component cannot be an alternative of itself."))
            if alternative.product_id.product_tmpl_id == alternative.bom_line_id.bom_id.product_tmpl_id:
                raise ValidationError(self.env._("The product to manufacture cannot be its own alternative component."))

    @api.constrains("product_qty")
    def _check_product_qty(self):
        for alternative in self:
            if alternative.product_qty <= 0:
                raise ValidationError(self.env._("The quantity of an alternative component must be positive."))

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for alternative in self:
            if alternative.date_start and alternative.date_end and alternative.date_start > alternative.date_end:
                raise ValidationError(self.env._("The validity start date must be before the end date."))

    def _is_valid_on(self, date):
        self.ensure_one()
        if self.date_start and date < self.date_start:
            return False
        if self.date_end and date > self.date_end:
            return False
        return True

    def _from_original_qty(self, qty, uom):
        """Quantity of the alternative, in its own unit, that replaces ``qty`` of the original component in ``uom``."""
        self.ensure_one()
        line = self.bom_line_id
        qty_line = uom._compute_quantity(qty, line.uom_id, round=False)
        return qty_line * self.product_qty / line.product_qty

    def _to_original_qty(self, qty, uom, original_uom):
        """Quantity of the original component, in ``original_uom``, replaced by ``qty`` of the alternative in ``uom``."""
        self.ensure_one()
        line = self.bom_line_id
        qty_alternative = uom._compute_quantity(qty, self.product_uom_id, round=False)
        qty_line = qty_alternative * line.product_qty / self.product_qty
        return line.uom_id._compute_quantity(qty_line, original_uom, round=False)
