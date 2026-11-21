# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

import json

from odoo import Command, api, fields, models
from odoo.exceptions import UserError

# Header fields that must be the same on every quotation; fields missing
# on the database (e.g. warehouse_id without sale_stock) are skipped.
SAME_VALUE_FIELDS = [
    "partner_id",
    "partner_invoice_id",
    "partner_shipping_id",
    "currency_id",
    "pricelist_id",
    "fiscal_position_id",
    "payment_term_id",
    "warehouse_id",
    "incoterm",
]
# Differences in these fields do not block the merge, the target's value is kept.
WARN_VALUE_FIELDS = ["user_id", "team_id"]


class SaleOrderMerge(models.TransientModel):
    _name = "sale.order.merge"
    _description = "Merge Quotations"

    order_ids = fields.Many2many("sale.order", string="Quotations", required=True)
    target_mode = fields.Selection(
        [
            ("oldest", "The oldest selected quotation"),
            ("selected", "A selected quotation"),
            ("new", "A new quotation"),
        ],
        string="Merge Into",
        default="oldest",
        required=True,
    )
    target_order_id = fields.Many2one("sale.order", string="Target Quotation")
    line_mode = fields.Selection(
        [
            ("sum", "Add up identical lines"),
            ("keep", "Keep all lines"),
        ],
        string="Lines",
        default="sum",
        required=True,
    )
    add_sections = fields.Boolean(
        string="Add a Section per Quotation",
        help="Add a section with the quotation number before the lines taken from each merged quotation.",
    )
    warning = fields.Text(compute="_compute_warning")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "sale.order" and self.env.context.get("active_ids"):
            res["order_ids"] = [Command.set(self.env.context["active_ids"])]
        return res

    @api.depends("order_ids")
    def _compute_warning(self):
        for wizard in self:
            messages = []
            for fname in WARN_VALUE_FIELDS:
                if fname not in wizard.order_ids._fields:
                    continue
                values = wizard.order_ids.mapped(fname)
                if len(values) > 1:
                    label = wizard.order_ids._fields[fname]._description_string(self.env)
                    messages.append(
                        self.env._(
                            "%(field)s is different (%(values)s), the one on the target quotation is kept.",
                            field=label,
                            values=", ".join(values.mapped("display_name")),
                        )
                    )
            wizard.warning = "\n".join(messages)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    def _check_orders(self):
        orders = self.order_ids
        if len(orders) < 2:
            raise UserError(self.env._("Select at least two quotations to merge."))
        orders.check_access("write")
        wrong_state = orders.filtered(lambda o: o.state not in ("draft", "sent"))
        if wrong_state:
            raise UserError(
                self.env._(
                    "Only quotations can be merged. These documents are confirmed, locked or cancelled: %s",
                    ", ".join(wrong_state.mapped("name")),
                )
            )
        if len(orders.company_id) > 1:
            raise UserError(self.env._("The quotations must belong to the same company."))
        for fname in SAME_VALUE_FIELDS:
            if fname not in orders._fields:
                continue
            if len(orders.mapped(fname)) > 1:
                label = orders._fields[fname]._description_string(self.env)
                details = "\n".join(f"{order.name}: {order[fname].display_name or '-'}" for order in orders)
                raise UserError(
                    self.env._(
                        "The quotations cannot be merged, %(field)s is different:\n%(details)s",
                        field=label,
                        details=details,
                    )
                )
        engaged = orders.filtered(
            # transaction_ids is restricted to invoicing users; a salesman must still see a started payment
            lambda o: o.signature
            or any(tx.state in ("pending", "authorized", "done") for tx in o.sudo().transaction_ids)
        )
        if engaged:
            raise UserError(
                self.env._(
                    "These quotations were already signed or have an online payment started: %s",
                    ", ".join(engaged.mapped("name")),
                )
            )

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------
    @api.model
    def _line_key(self, line):
        distribution = json.dumps(line.analytic_distribution or {}, sort_keys=True)
        return (
            line.product_id.id,
            line.name,
            line.product_uom_id.id,
            line.price_unit,
            line.discount,
            tuple(sorted(line.tax_ids.ids)),
            distribution,
        )

    def _get_target(self):
        orders = self.order_ids.sorted(lambda o: (o.date_order or o.create_date, o.id))
        if self.target_mode == "oldest":
            return orders[0], False
        if self.target_mode == "selected":
            if not self.target_order_id or self.target_order_id not in self.order_ids:
                raise UserError(self.env._("Choose the target quotation among the selected ones."))
            return self.target_order_id, False
        target = orders[0].copy({"order_line": [], "origin": False, "client_order_ref": False})
        return target, True

    @api.model
    def _join_unique(self, values):
        seen = []
        for value in values:
            for part in (value or "").split(", "):
                if part and part not in seen:
                    seen.append(part)
        return ", ".join(seen)

    def action_merge(self):
        self.ensure_one()
        self._check_orders()
        target, is_new = self._get_target()
        sources = self.order_ids - target
        orders = (self.order_ids | target) if is_new else self.order_ids
        # copying the lines of the sources: they stay unchanged on the cancelled quotations
        existing = {}
        if self.line_mode == "sum":
            for line in target.order_line.filtered(lambda line: not line.display_type):
                existing.setdefault(self._line_key(line), line)
        sequence = max(target.order_line.mapped("sequence") or [0])
        for source in sources if not is_new else self.order_ids:
            lines = source.order_line.sorted("sequence")
            if self.add_sections and lines:
                sequence += 1
                self.env["sale.order.line"].create(
                    {
                        "order_id": target.id,
                        "display_type": "line_section",
                        "name": source.name,
                        "sequence": sequence,
                    }
                )
            for line in lines:
                if self.line_mode == "sum" and not line.display_type:
                    key = self._line_key(line)
                    if key in existing:
                        existing[key].product_uom_qty += line.product_uom_qty
                        continue
                sequence += 1
                new_line = line.copy({"order_id": target.id, "sequence": sequence})
                if self.line_mode == "sum" and not line.display_type:
                    existing[self._line_key(line)] = new_line
        merged = self.order_ids if is_new else sources
        values = {
            "origin": self._join_unique(orders.mapped("origin")),
            "client_order_ref": self._join_unique(orders.mapped("client_order_ref")),
        }
        validity = [date for date in orders.mapped("validity_date") if date]
        if validity:
            values["validity_date"] = min(validity)
        target.write(values)
        target.message_subscribe(partner_ids=merged.message_partner_ids.ids)
        merged.write({"merged_into_id": target.id})
        merged._action_cancel()
        target.message_post(body=self.env._("Quotations merged into this one: %s", ", ".join(merged.mapped("name"))))
        for order in merged:
            order.message_post(body=self.env._("Merged into %s", target._get_html_link()))
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": target.id,
            "view_mode": "form",
            "target": "current",
        }
