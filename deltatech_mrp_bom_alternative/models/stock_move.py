from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    bom_line_alternative_id = fields.Many2one(
        "mrp.bom.line.alternative", string="Alternative Rule", index="btree_not_null", readonly=True
    )
    original_product_id = fields.Many2one(
        "product.product", string="Replaced Component", index="btree_not_null", readonly=True
    )
    substitution_reason = fields.Selection(
        [("manual", "Manual"), ("auto", "Automatic")], string="Substitution", readonly=True
    )
    has_bom_alternatives = fields.Boolean(compute="_compute_has_bom_alternatives")

    @api.depends("bom_line_id.alternative_ids", "bom_line_alternative_id")
    def _compute_has_bom_alternatives(self):
        for move in self:
            move.has_bom_alternatives = bool(move.bom_line_id.alternative_ids) and not move.bom_line_alternative_id

    def _get_alternative_free_qty(self, product, allocated):
        """Free quantity of ``product`` in the source location of the move, in the product unit,
        less what the current substitution run has already allocated."""
        self.ensure_one()
        free_qty = product.with_context(location=self.location_id.id).free_qty
        return max(free_qty - allocated.get(product, 0.0), 0.0)

    def _get_bom_alternative_original_qty(self, qty):
        """Quantity of the original component of the BoM line, in the line unit, covered by ``qty`` of this move."""
        self.ensure_one()
        line = self.bom_line_id
        if self.bom_line_alternative_id:
            return self.bom_line_alternative_id._to_original_qty(qty, self.uom_id, line.uom_id)
        return self.uom_id._compute_quantity(qty, line.uom_id, round=False)

    def action_open_bom_alternative_substitute(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Substitute Component"),
            "res_model": "mrp.bom.alternative.substitute",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_id": self.id},
        }

    def _substitute_with_alternative(self, alternative, qty, reason):
        """Replace ``qty`` (in the move unit) of this component move by ``alternative``.

        The original move keeps the rest of its demand, or is dropped when nothing is left, and a new
        component move is added on the same BoM line and operation. Returns the new move.
        """
        self.ensure_one()
        production = self.raw_material_production_id
        alternative_qty = alternative.product_uom_id.round(
            alternative._from_original_qty(qty, self.uom_id), rounding_method="UP"
        )
        values = production._get_move_raw_values(
            alternative.product_id,
            alternative_qty,
            alternative.product_uom_id,
            operation_id=self.operation_id.id,
            bom_line=self.bom_line_id,
        )
        values.update(
            {
                "sequence": self.sequence,
                "location_id": self.location_id.id,
                "bom_line_alternative_id": alternative.id,
                "original_product_id": self.product_id.id,
                "substitution_reason": reason,
            }
        )
        new_move = self.create(values)

        original_product = self.product_id
        original_uom = self.uom_id
        remaining = self.product_uom_qty - qty
        if self.uom_id.compare(remaining, 0) <= 0:
            if self.state == "draft":
                self.unlink()
            else:
                self.product_uom_qty = 0
                self._action_cancel()
        else:
            self.product_uom_qty = remaining

        if production.state != "draft":
            new_move._action_confirm(merge=False)
            new_move._action_assign()

        production.message_post(
            body=self.env._(
                "%(qty)s %(uom)s of %(original)s replaced by %(alt_qty)s %(alt_uom)s of %(alternative)s (%(reason)s).",
                qty=original_uom.round(qty),
                uom=original_uom.name,
                original=original_product.display_name,
                alt_qty=alternative_qty,
                alt_uom=alternative.product_uom_id.name,
                alternative=alternative.product_id.display_name,
                reason=dict(self._fields["substitution_reason"]._description_selection(self.env))[reason],
            )
        )
        return new_move
