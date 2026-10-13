# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    postponed = fields.Boolean(string="Postponed")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _default_postponed(self):
        picking_type = self.env["stock.picking.type"].browse(self.env.context.get("default_picking_type_id"))

        return picking_type.postponed

    postponed = fields.Boolean(
        string="Postponed",
        tracking=True,
        default=lambda self: self._default_postponed(),
    )
    delivery_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready_in_warehouse", "Ready in warehouse"),  # coletul este in depozit
            ("pre_advice", "Pre advice"),  # awb generat
            ("in_transit", "In Transit"),  # colet ridicat de curier defi a fsot facuta expedierea
            ("in_warehouse", "In Carrier Warehouse"),  # colet in depozitul curierului
            ("in_delivery", "In delivery"),  # coletul este in livrare
            ("delivered", "Delivered"),  # coletul a fost livrat
            ("refused", "Refused"),  # coletul a fost refuzat
            # ("return_by_sender", "Return by Sender"),  # coletul a fost returnat la cererea expeditorului
            # ("cancelled", "Cancelled"),  # coletul a fost anulat
        ],
        string="Delivery State",
        default="draft",
        readonly=False,
        tracking=True,
    )
    available_state = fields.Selection(
        [
            ("unavailable", "Unavailable"),
            ("partially", "Partially available"),
            ("available", "Available"),
        ],
        default=False,
        store=True,
        compute="_compute_state",
    )

    # Validating a transfer no longer writes `delivery_state = delivered` when no
    # carrier is found. That test read an unfinished transfer as a finished
    # delivery: with a shipping integration at `rate` level the operator
    # validates first and sends to the shipper afterwards, so `carrier_id` is
    # empty on both the picking and the order for as long as the shipping wizard
    # takes, and the parcel went to `delivered` — pushing the order to its
    # delivered phase — while the label was still being printed. The two cases
    # (a transfer that will never have a carrier, and one that does not have it
    # *yet*) are indistinguishable at validation time; what separates them is
    # whether an AWB shows up afterwards. The delivery status cron in
    # `deltatech_delivery` therefore marks the carrier-less transfers as
    # delivered once a grace period has passed without one.

    @api.depends("move_type", "move_ids.state", "move_ids.picking_id", "postponed")
    def _compute_state(self):
        res = super()._compute_state()

        for picking in self.filtered(lambda p: p.state == "assigned"):
            if picking.postponed:
                picking.state = "waiting"

        picking_in_progress = self.filtered(lambda p: p.state in ["assigned", "waiting", "confirmed"])
        remaining = self - picking_in_progress
        for picking in picking_in_progress:
            move_state = picking.move_ids._get_relevant_state_among_moves()
            map_state = {"assigned": "available", "partially_available": "partially"}
            picking.available_state = map_state.get(move_state, "unavailable")

        remaining.available_state = False
        return res

    def button_validate(self):
        for picking in self:
            if picking.postponed:
                raise UserError(self.env._("The transfer %s is postponed", picking.name))

        return super().button_validate()

    def _create_backorder(self):
        backorders = super()._create_backorder()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        postponed = get_param("backorders.postponed", default="False")
        postponed = safe_eval(postponed)
        if postponed:
            backorders.write({"postponed": True})
        return backorders
