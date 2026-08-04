# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import uuid

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_rfq_send(self):
        self.order_line.with_context(backend=True).check_extra_product()
        return super().action_rfq_send()

    def print_quotation(self):
        self.order_line.with_context(backend=True).check_extra_product()
        return super().print_quotation()

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
    extra_price_computed = fields.Float(
        digits="Product Price",
        copy=False,
        help="Technical field: last unit price computed for this extra line. "
        "A unit price that differs from it was set by the user and is kept as is.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for line in res:
            line.check_extra_product()
        return res

    def unlink(self):
        for line in self:
            if line.product_id.extra_product_id:
                extra_line_id = line.order_id.order_line.filtered(
                    lambda l: line.line_uuid is not False and l.line_uuid == line.line_uuid and l.id != line.id
                )
                if extra_line_id:
                    extra_line_id.unlink()
        return super().unlink()

    def _has_manual_price(self):
        """Tell whether the unit price of this extra line was set by the user.

        The price is considered manual when it differs from what this module
        computed last (``extra_price_computed``). Unlike the sale order line,
        ``purchase.order.line`` has no ``technical_price_unit`` in this version,
        so a vendor price recomputation on the extra line itself is kept as well.
        """
        self.ensure_one()
        # `currency_id` can be False on NewId records
        currency = self.currency_id or self.company_id.currency_id or self.env.company.currency_id
        return bool(currency.compare_amounts(self.extra_price_computed, self.price_unit))

    def check_extra_product(self):
        for line in self:
            if line.order_id.state not in ["draft", "sent"]:
                continue
            if not line.product_id.extra_product_id:
                continue
            extra_product = line.product_id.extra_product_id
            extra_line_id = line.order_id.order_line.filtered(
                lambda l: line.line_uuid is not False and l.line_uuid == line.line_uuid and l.id != line.id
            )
            new_line = not extra_line_id
            if new_line:
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
            # a price typed in on the extra line wins over the computed one, until the
            # extra line is deleted (it is then regenerated with the computed price)
            manual_price = None
            if not new_line and extra_line_id._has_manual_price():
                manual_price = extra_line_id.price_unit
            product_qty = line.product_qty * (line.product_id.extra_qty or 1.0)
            if product_qty != extra_line_id.product_qty:
                extra_line_id.product_qty = product_qty
                if manual_price is not None:
                    # the standard recomputes the price from the vendor on a quantity
                    # change, so the manual price has to be written back
                    extra_line_id.price_unit = manual_price
            if manual_price is not None or not line.product_id.extra_percent:
                continue
            price_unit = line.price_unit * (line.product_id.extra_percent or 0.0) / 100.0
            # keep track of the price we set, so that a later manual change is recognized
            extra_line_id.update({"price_unit": price_unit, "extra_price_computed": price_unit})
