# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


import uuid

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line")
    def onchange_order_line(self):
        """
        Update extra product in backend
        :return: super
        """
        self.order_line.with_context(backend=True).check_extra_product()

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res = super()._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            **kwargs,
        )
        if res["line_id"]:
            line_id = self.env["sale.order.line"].browse(res["line_id"])
            if res["quantity"]:
                line_id.check_extra_product()
                parent_line_id = self.order_line.filtered(
                    lambda li: li.line_uuid is not False
                    and li.line_uuid == line_id.line_uuid
                    and li.id != line_id.id
                    and li.product_id.extra_product_id
                )
                if parent_line_id:
                    parent_line_id.check_extra_product()
            else:
                # seems like delete, checking all lines
                lines = self.order_line
                lines.check_extra_product()
        else:
            # seems like delete, checking all lines
            lines = self.order_line
            lines.check_extra_product()
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    line_uuid = fields.Char()

    def unlink(self):
        for line in self:
            if line.product_id.extra_product_id:
                extra_line_id = self.order_id.order_line.filtered(
                    lambda li, line_uuid=line.line_uuid, line_id=line.id: li.line_uuid is not False
                    and li.line_uuid == line_uuid
                    and li.id != line_id
                )
                if extra_line_id:
                    extra_line_id.unlink()
        return super().unlink()

    def check_extra_product(self):
        for line in self:
            if line.product_id.extra_product_id:
                extra_line_id = self.order_id.order_line.filtered(
                    lambda li, line_uuid=line.line_uuid, line_id=line.id: li.line_uuid is not False
                    and li.line_uuid == line_uuid
                    and li.id != line_id
                )
                if not extra_line_id:
                    new_uuid = str(uuid.uuid4())
                    values = {
                        "product_uom_qty": line.product_uom_qty * (line.product_id.extra_qty or 1.0),
                        "product_id": line.product_id.extra_product_id.id,
                        "state": "draft",
                        "order_id": self.order_id.id,
                        "sequence": line.sequence + 1,
                        "line_uuid": new_uuid,
                    }
                    backend = self.env.context.get("backend", False)
                    if backend:
                        extra_line_id = line.order_id.order_line.new(values)
                    else:
                        extra_line_id = line.order_id.order_line.create(values)
                    line.line_uuid = new_uuid

                extra_line_id.product_uom_qty = line.product_uom_qty * (line.product_id.extra_qty or 1.0)
                if line.product_id.extra_percent:
                    extra_line_id.price_unit = line.price_unit * (line.product_id.extra_percent or 0.0) / 100.0
                else:
                    extra_line_id.price_unit = line.product_id.extra_product_id.lst_price
