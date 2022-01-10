# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class StockPicking(models.Model):
    _inherit = "stock.picking"

    postponed = fields.Boolean(
        string="Postponed",
        tracking=True,
        states={"done": [("readonly", True)], "cancel": [("readonly", True)]},
    )
    delivery_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pre_advice", "Pre advice"),  # awb generat
            ("in_transit", "In Transit"),  # colet ridicat de curier
            ("in_warehouse", "In Warehouse"),  # colet in depozitul curierului
            ("in_delivery", "In delivery"),  # coletul este livrare
            ("delivered", "Delivered"),
        ],
        string="State",
        default="draft",
        readonly=False,
    )
    available_state = fields.Selection(
        [("unavailable", "unavailable"), ("partially", "Partially available"), ("available", "Available")],
        default=False,
        store=True,
        compute="_compute_state",
    )

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            if picking.state == "done" and not picking.carrier_id:
                picking.write({"delivery_state": "delivered"})
        return res

    @api.depends("move_type", "immediate_transfer", "move_lines.state", "move_lines.picking_id", "postponed")
    def _compute_state(self):
        super(StockPicking, self)._compute_state()

        for picking in self.filtered(lambda p: p.state == "assigned"):
            if picking.postponed:
                picking.state = "waiting"

        picking_in_progress = self.filtered(lambda p: p.state in ["assigned", "waiting", "confirmed"])
        remaining = self - picking_in_progress
        for picking in picking_in_progress:
            move_state = picking.move_lines._get_relevant_state_among_moves()
            map_state = {"assigned": "available", "partially_available": "partially"}
            picking.available_state = map_state.get(move_state, "unavailable")

        remaining.available_state = False

    def button_validate(self):
        for picking in self:
            if picking.postponed:
                raise UserError(_("The transfer %s is postponed") % picking.name)

        return super(StockPicking, self).button_validate()

    def _create_backorder(self):
        backorders = super(StockPicking, self)._create_backorder()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        postponed = get_param("backorders.postponed", default="False")
        postponed = safe_eval(postponed)
        if postponed:
            backorders.write({"postponed": True})
        return backorders
