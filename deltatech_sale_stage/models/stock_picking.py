# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    stage_id = fields.Many2one("sale.order.stage", string="Stage", copy=False)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            if picking.sale_id:
                stage = picking.picking_type_id.stage_id
                if not stage:
                    picking.sale_id.set_stage("delivered")
                else:
                    picking.sale_id.stage_id = stage

        return res
