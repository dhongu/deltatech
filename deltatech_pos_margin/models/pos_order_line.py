# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    margin = fields.Float(
        "Margin", compute="_compute_margin", digits="Product Price", store=True, groups="base.group_user"
    )
    margin_percent = fields.Float("Margin (%)", compute="_compute_margin", store=True, groups="base.group_user")
    purchase_price = fields.Float(
        string="Cost",
        compute="_compute_purchase_price",
        digits="Product Price",
        store=True,
        readonly=False,
        groups="base.group_user",
    )

    @api.depends("product_id", "company_id", "currency_id", "product_uom_id")
    def _compute_purchase_price(self):
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line = line.with_context(force_company=line.company_id.id)
            product = line.product_id
            product_cost = product.standard_price
            if not product_cost:
                # If the standard_price is 0
                # Avoid unnecessary computations
                # and currency conversions
                line.purchase_price = 0.0
                continue
            fro_cur = product.cost_currency_id
            to_cur = line.currency_id or line.order_id.currency_id
            if line.product_uom_id and line.product_uom_id != product.uom_id:
                product_cost = product.uom_id._compute_price(product_cost, line.product_uom_id)
            line.purchase_price = (
                fro_cur._convert(
                    from_amount=product_cost,
                    to_currency=to_cur,
                    company=line.company_id or self.env.company,
                    date=line.order_id.date_order or fields.Date.today(),
                    round=False,
                )
                if to_cur and product_cost
                else product_cost
            )
            # The pricelist may not have been set, therefore no conversion
            # is needed because we don't know the target currency..

    @api.depends("price_subtotal", "qty", "purchase_price")
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - (line.purchase_price * line.qty)
            line.margin_percent = line.price_subtotal and line.margin / line.price_subtotal
