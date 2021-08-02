# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_simple_mrp_id = fields.Many2one("sale.order", string="Sales Order", store=True, readonly=False)

    def update_mrp_svl(self):
        # function for recompute in svl's from the out svl's
        for picking in self:
            if picking.sale_simple_mrp_id:
                sale_order = self.sale_simple_mrp_id
                mrp_pickings = sale_order.simple_mrp_picking_ids
                other_pickings = mrp_pickings - picking
                consumed_value = other_pickings.get_out_svl()
                svls = picking.move_lines.stock_valuation_layer_ids
                init_value = 0.0
                for svl in svls:
                    init_value += svl.value
                if init_value != consumed_value:
                    diff = consumed_value - init_value
                    if len(svls) == 1:
                        new_svl = svls.copy()
                        new_svl.update({
                            "unit_cost": diff / svls.quantity,
                            "value": diff,
                            "quantity": 0.0,
                            "description": "mrp_simple reevaluation, SO " + sale_order.name
                        })

    def get_out_svl(self):
        value = 0.0
        for picking in self:
            svls = picking.move_lines.stock_valuation_layer_ids
            for svl in svls:
                value += svl.value
        return abs(value)

