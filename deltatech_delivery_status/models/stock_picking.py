# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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

    def button_validate(self):
        for picking in self:
            if picking.postponed:
                raise UserError(_("The transfer %s is postponed") % picking.name)

        return super(StockPicking, self).button_validate()
