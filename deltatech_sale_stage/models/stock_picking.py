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
                if not phase:
                    picking.sale_id.set_phase("delivered")
                else:
                    picking.sale_id.phase_id = phase

        return res
