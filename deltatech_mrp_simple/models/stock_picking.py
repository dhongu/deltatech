# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_simple_mrp_id = fields.Many2one("sale.order", string="Sales Order", store=True, readonly=False)

    def update_mrp_svl(self):
        # function for recompute in svl's from the out svl's
        for picking in self:
            if picking.sale_simple_mrp_id:
                sale_order = self.sale_simple_mrp_id
                other_pickings = sale_order.simple_mrp_picking_ids - picking
                consumed_value = other_pickings.get_out_svl()
                svls = picking.move_lines.stock_valuation_layer_ids
                if len(svls) == 1:
                    new_svl = svls.copy()
                    new_svl.update(
                        {
                            "unit_cost": consumed_value / svls.quantity,
                            "value": consumed_value,
                        }
                    )
                    svls.unlink()
                    picking.move_lines.correction_valuation()
                    _logger.info("Corrected svl for mrp pick %s" % picking.name)
                delivery_pickings = sale_order.picking_ids
                if len(delivery_pickings) == 1:
                    moves = delivery_pickings.move_lines
                    if len(moves) == 1:
                        moves.price_unit = consumed_value
                    svls = delivery_pickings.move_lines.stock_valuation_layer_ids
                    if len(svls) == 1:
                        new_svl = svls.copy()
                        new_svl.update(
                            {
                                "unit_cost": consumed_value / svls.quantity,
                                "value": consumed_value,
                            }
                        )
                        svls.unlink()
                        delivery_pickings.move_lines.correction_valuation()
                        _logger.info("Corrected svl for delivery pick %s" % delivery_pickings.name)

    def get_out_svl(self):
        value = 0.0
        for picking in self:
            svls = picking.move_lines.stock_valuation_layer_ids
            for svl in svls:
                value += svl.value
        return abs(value)
