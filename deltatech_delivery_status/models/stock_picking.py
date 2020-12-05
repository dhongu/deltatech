# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

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

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for picking in self:
            if picking.state == "done" and not picking.carrier_id:
                picking.write({"delivery_state": "delivered"})

        return res
