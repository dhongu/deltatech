from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import UserError


class MrpBomAlternativeSubstitute(models.TransientModel):
    _name = "mrp.bom.alternative.substitute"
    _description = "Substitute Component with an Alternative"

    move_id = fields.Many2one("stock.move", string="Component Move", required=True, readonly=True)
    production_id = fields.Many2one(related="move_id.raw_material_production_id")
    product_id = fields.Many2one(related="move_id.product_id", string="Component")
    product_uom = fields.Many2one(related="move_id.product_uom")
    product_uom_qty = fields.Float(related="move_id.product_uom_qty", string="To Consume")
    reserved_qty = fields.Float(compute="_compute_quantities", string="Reserved", digits="Product Unit")
    max_qty = fields.Float(compute="_compute_quantities", string="Replaceable", digits="Product Unit")
    qty = fields.Float(
        string="Quantity to Replace",
        digits="Product Unit",
        compute="_compute_qty",
        store=True,
        readonly=False,
        help="Quantity of the original component, in its unit, consumed from the alternative instead.",
    )
    allowed_alternative_ids = fields.Many2many("mrp.bom.line.alternative", compute="_compute_allowed_alternative_ids")
    alternative_id = fields.Many2one(
        "mrp.bom.line.alternative",
        string="Alternative",
        required=True,
        domain="[('id', 'in', allowed_alternative_ids)]",
    )
    alternative_qty = fields.Float(
        compute="_compute_alternative_qty", string="Alternative Quantity", digits="Product Unit"
    )
    alternative_uom_id = fields.Many2one(related="alternative_id.product_uom_id", string="Alternative Unit")
    availability_html = fields.Html(compute="_compute_availability_html", sanitize=False)

    @api.depends("move_id")
    def _compute_quantities(self):
        for wizard in self:
            move = wizard.move_id
            wizard.reserved_qty = move.quantity if move.state != "draft" else 0.0
            wizard.max_qty = move.product_uom_qty - (move.quantity if move.picked else 0.0)

    @api.depends("move_id")
    def _compute_qty(self):
        for wizard in self:
            wizard.qty = wizard.move_id.product_uom_qty - wizard.reserved_qty or wizard.max_qty

    @api.depends("move_id")
    def _compute_allowed_alternative_ids(self):
        for wizard in self:
            date = fields.Date.to_date(wizard.production_id.date_start) or fields.Date.context_today(wizard)
            wizard.allowed_alternative_ids = wizard.move_id.bom_line_id._get_valid_alternatives(date)

    @api.depends("alternative_id", "qty")
    def _compute_alternative_qty(self):
        for wizard in self:
            if wizard.alternative_id:
                wizard.alternative_qty = wizard.alternative_id._from_original_qty(wizard.qty, wizard.product_uom)
            else:
                wizard.alternative_qty = 0.0

    @api.depends("move_id", "qty")
    def _compute_availability_html(self):
        for wizard in self:
            move = wizard.move_id
            rows = []
            location = move.location_id
            original = move.product_id.with_context(location=location.id)
            rows.append(
                (
                    original.display_name,
                    self.env._("Original"),
                    wizard.qty,
                    move.product_uom,
                    original.uom_id._compute_quantity(original.free_qty, move.product_uom),
                    original.uom_id._compute_quantity(original.virtual_available, move.product_uom),
                )
            )
            for alternative in wizard.allowed_alternative_ids:
                product = alternative.product_id.with_context(location=location.id)
                uom = alternative.product_uom_id
                rows.append(
                    (
                        product.display_name,
                        alternative.note or "",
                        alternative._from_original_qty(wizard.qty, move.product_uom),
                        uom,
                        product.uom_id._compute_quantity(product.free_qty, uom),
                        product.uom_id._compute_quantity(product.virtual_available, uom),
                    )
                )
            header = Markup(
                "<thead><tr><th>%s</th><th>%s</th><th class='text-end'>%s</th>"
                "<th class='text-end'>%s</th><th class='text-end'>%s</th></tr></thead>"
            ) % (
                self.env._("Component"),
                self.env._("Note"),
                self.env._("Needed"),
                self.env._("Free"),
                self.env._("Forecasted"),
            )
            body = Markup("").join(
                Markup(
                    "<tr><td>%s</td><td>%s</td><td class='text-end'>%s %s</td>"
                    "<td class='text-end'>%s</td><td class='text-end'>%s</td></tr>"
                )
                % (
                    escape(name),
                    escape(note),
                    uom.round(needed),
                    escape(uom.name),
                    uom.round(free),
                    uom.round(forecast),
                )
                for name, note, needed, uom, free, forecast in rows
            )
            wizard.availability_html = Markup(
                "<table class='table table-sm o_main_table'>%s<tbody>%s</tbody></table>"
            ) % (
                header,
                body,
            )

    def action_substitute(self):
        self.ensure_one()
        move = self.move_id
        if move.state in ("done", "cancel"):
            raise UserError(self.env._("The component move is already done or cancelled."))
        if move.product_uom.compare(self.qty, 0) <= 0:
            raise UserError(self.env._("The quantity to replace must be positive."))
        if move.product_uom.compare(self.qty, self.max_qty) > 0:
            raise UserError(
                self.env._(
                    "You cannot replace more than %(qty)s %(uom)s.",
                    qty=move.product_uom.round(self.max_qty),
                    uom=move.product_uom.name,
                )
            )
        if self.alternative_id not in self.allowed_alternative_ids:
            raise UserError(self.env._("This alternative is not valid for the component on the order date."))
        unreserve = (
            move.state != "draft" and move.product_uom.compare(self.qty, move.product_uom_qty - move.quantity) > 0
        )
        if unreserve:
            move._do_unreserve()
        move._substitute_with_alternative(self.alternative_id, self.qty, "manual")
        if unreserve and move.exists() and move.state not in ("done", "cancel"):
            move._action_assign()
        return {"type": "ir.actions.act_window_close"}
