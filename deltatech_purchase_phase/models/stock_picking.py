# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self, vals):
        delivery_state = vals.get("delivery_state")
        if delivery_state:
            if delivery_state == "pre_advice":
                phase = "pre_advice"
            elif delivery_state in ("in_transit", "in_warehouse", "in_delivery"):
                phase = "shipped"
            elif delivery_state == "delivered":
                phase = "delivered"
            elif delivery_state == "refused":
                phase = "refused"
            else:
                phase = None

            if phase:
                for picking in self.filtered("purchase_id"):
                    picking.purchase_id.set_phase(phase)

        return super().write(vals)
