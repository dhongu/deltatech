from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    color_trigger = fields.Selection(
        [("danger", "Danger"), ("warning", "Warning")],
        string="Trigger",
        compute="_compute_color_trigger",
    )

    @api.depends("purchase_line_id", "sale_line_ids")
    def _compute_color_trigger(self):
        for line in self:
            color_trigger = False
            if line.move_id.move_type not in (
                "in_invoice",
                "in_refund",
                "out_invoice",
                "out_refund",
            ):
                line.color_trigger = color_trigger
                continue
            if not line.product_id:
                color_trigger = "warning"
            else:
                if line.product_id.type == "consu" and line.product_id.is_storable is True:
                    if line.move_id.move_type in ("in_invoice", "in_refund"):
                        if not line.purchase_line_id:
                            color_trigger = "danger"
                    else:
                        if not line.sale_line_ids:
                            color_trigger = "danger"

            line.color_trigger = color_trigger


class AccountMove(models.Model):
    _inherit = "account.move"

    color_triggered = fields.Boolean(string="Trigger", compute="_compute_color_trigger")

    @api.depends("invoice_line_ids")
    def _compute_color_trigger(self):
        for move in self:
            color_triggered = False
            for line in move.invoice_line_ids:
                if line.color_trigger or not line.product_uom_id:
                    color_triggered = True
                    continue
            move.color_triggered = color_triggered
