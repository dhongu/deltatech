# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    phase_id = fields.Many2one("sale.order.phase", string="Phase", copy=False)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            if picking.sale_id:
                phase = picking.picking_type_id.phase_id
                if phase:
                    picking.sale_id.phase_id = phase
        return res

    def write(self, vals):
        if "delivery_state" in vals:
            if vals["delivery_state"] in ["in_transit", "in_warehouse", "in_delivery"]:
                for picking in self:
                    if picking.sale_id:
                        picking.sale_id.set_phase("shipped")
            if vals["delivery_state"] == "delivered":
                for picking in self:
                    if picking.sale_id:
                        picking.sale_id.set_phase("delivered")
            if vals["delivery_state"] == "pre_advice":
                for picking in self:
                    if picking.sale_id:
                        picking.sale_id.set_phase("pre_advice")

        return super().write(vals)
