# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_refurbish = fields.Boolean()

    def _update_reserved_quantity(
        self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True
    ):
        if self.sale_line_id and self.sale_line_id.lot_id:
            lot_id = self.sale_line_id.lot_id
        return super(StockMove, self)._update_reserved_quantity(
            need, available_quantity, location_id, lot_id, package_id, owner_id, strict
        )

    # def _should_bypass_reservation(self):
    #     res = super(StockMove, self)._should_bypass_reservation()
    #     if not res and self.sale_line_id and self.sale_line_id.lot_id:
    #         res = True
    #     return res

    # def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
    #     vals = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
    #     if self.sale_line_id and self.sale_line_id.lot_id:
    #         vals['lot_id'] = self.sale_line_id.lot_id.id
    #     return vals
