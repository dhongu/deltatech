# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import uuid

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange("order_line")
    def onchange_order_line(self):
        """
        Update extra product in backend
        :return: super
        """
        self.order_line.with_context(backend=True).check_extra_product()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    line_uuid = fields.Char()

    def unlink(self):
        for line in self:
            if line.product_id.extra_product_id:
                extra_line_id = self.order_id.order_line.filtered(
                    lambda l: line.line_uuid is not False and l.line_uuid == line.line_uuid and l.id != line.id
                )
                if extra_line_id:
                    extra_line_id.unlink()
        return super().unlink()

    def check_extra_product(self):
        for line in self:
            if line.order_id.state not in ["draft", "sent"]:
                continue
            if line.product_id.extra_product_id:
                extra_product = line.product_id.extra_product_id
                extra_line_id = self.order_id.order_line.filtered(
                    lambda l: line.line_uuid is not False and l.line_uuid == line.line_uuid and l.id != line.id
                )
                if not extra_line_id:
                    new_uuid = str(uuid.uuid4())
                    values = {
                        "product_qty": line.product_qty * (line.product_id.extra_qty or 1.0),
                        "product_id": extra_product.id,
                        "product_uom": extra_product.uom_id.id,
                        "state": "draft",
                        "order_id": line.order_id.id,
                        "sequence": line.sequence + 1,
                        "line_uuid": new_uuid,
                    }
                    backend = self.env.context.get("backend", False)
                    if backend:
                        extra_line_id = line.order_id.order_line.new(values)
                    else:
                        extra_line_id = line.order_id.order_line.create(values)
                    line.line_uuid = new_uuid

                extra_line_id.product_qty = line.product_qty * (line.product_id.extra_qty or 1.0)
                if line.product_id.extra_percent:
                    extra_line_id.price_unit = line.price_unit * (line.product_id.extra_percent or 0.0) / 100.0
