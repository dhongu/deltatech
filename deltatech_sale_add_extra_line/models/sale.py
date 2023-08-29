# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


import uuid

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line")
    def onchange_order_line(self):
        for line in self.order_line:
            if line.product_id.extra_product_id:
                extra_line_id = self.order_line.filtered(
                    lambda l: line.line_uuid is not False and l.line_uuid == line.line_uuid and l.id != line.id
                )
                if not extra_line_id:
                    new_uuid = str(uuid.uuid4())
                    values = {
                        "product_uom_qty": line.product_uom_qty,
                        "product_id": line.product_id.extra_product_id,
                        "state": "draft",
                        "order_id": self.id,
                        "sequence": line.sequence + 1,
                        "line_uuid": new_uuid,
                    }
                    extra_line_id = line.order_id.order_line.new(values)
                    extra_line_id.product_id_change()
                    extra_line_id.product_uom_change()
                    line.line_uuid = new_uuid

                extra_line_id.product_uom_qty = line.product_uom_qty
                if line.product_id.extra_percent:
                    extra_line_id.price_unit = line.price_unit * (line.product_id.extra_percent or 0.0) / 100.0
                else:
                    extra_line_id.price_unit = line.product_id.extra_product_id.lst_price


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    line_uuid = fields.Char()
