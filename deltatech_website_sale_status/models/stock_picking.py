# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self, vals):
        if "delivery_state" in vals:
            if vals["delivery_state"] in ["in_transit", "in_warehouse", "in_delivery"]:
                for picking in self:
                    if picking.sale_id:
                        picking.sale_id.stage = "in_delivery"
            if vals["delivery_state"] == "delivered":
                for picking in self:
                    if picking.sale_id:
                        picking.sale_id.stage = "delivered"
            if vals["delivery_state"] == "pre_advice":
                for picking in self:
                    if picking.sale_id:
                        picking.sale_id.stage = "pre_advice"

        return super().write(vals)
