# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line")
    def onchange_order_line(self):
        for line in self.order_line:
            if line.product_id.extra_product_id:
                extra_line_id = self.order_line.filtered(lambda l: l.sequence == line.sequence + 1)
                if not extra_line_id:
                    values = {
                        "product_uom_qty": line.product_uom_qty,
                        "product_id": line.product_id.extra_product_id,
                        "state": "draft",
                        "order_id": self.id,
                        "sequence": line.sequence + 1,
                    }
                    extra_line_id = line.order_id.order_line.new(values)
                    extra_line_id.product_id_change()
                    extra_line_id.product_uom_change()

                extra_line_id.product_uom_qty = line.product_uom_qty
                extra_line_id.price_unit = line.price_unit * (line.product_id.extra_percent or 0.0) / 100.0
