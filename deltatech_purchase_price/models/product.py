# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(tracking=True)
    last_purchase_price = fields.Float(digits="Product Price", tracking=True, company_dependent=True)

    @api.onchange("last_purchase_price", "trade_markup")
    def onchange_last_purchase_price(self):
        self.product_tmpl_id.onchange_last_purchase_price()


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(tracking=True)
    list_price = fields.Float(tracking=True)
    last_purchase_price = fields.Float(
        digits="Product Price",
        compute="_compute_last_purchase_price",
        inverse="_inverse_last_purchase_price",
        search="_search_last_purchase_price",
        tracking=True,
        company_dependent=True,
    )

    @api.depends("product_variant_ids.last_purchase_price", "seller_ids.price", "seller_ids.product_id")
    @api.depends_context("company")
    def _compute_last_purchase_price(self):
        # Single-variant (and variant-less) templates keep the native behaviour:
        # the template value mirrors its only variant. For multi-variant
        # templates the native helper would fall back to 0 (variants may hold
        # different costs), which leaves the template price at 0 and breaks the
        # markup-based sale price. Instead we surface the most recently updated
        # supplier price, regardless of variant (ticket 8403).
        single = self.filtered(lambda t: len(t.product_variant_ids) <= 1)
        single._compute_template_field_from_variant_field("last_purchase_price")
        for template in self - single:
            template.last_purchase_price = template._get_last_purchase_price_from_sellers()

    def _get_last_purchase_price_from_sellers(self):
        """Last purchase price to show on a multi-variant template.

        Picks the purchase price of the variant tied to the most recently
        updated vendor line (``product.supplierinfo``); a template-level vendor
        line falls back to the first variant. When no vendor line yields a
        price, falls back to the highest known purchase price across variants,
        so the template never collapses to 0 while any variant has a cost.
        """
        self.ensure_one()
        sellers = self.seller_ids.sorted(key=lambda s: s.write_date or s.create_date, reverse=True)
        for seller in sellers:
            variant = seller.product_id or self.product_variant_ids[:1]
            if variant.last_purchase_price:
                return variant.last_purchase_price
        prices = [p for p in self.product_variant_ids.mapped("last_purchase_price") if p]
        return max(prices) if prices else 0.0

    def _inverse_last_purchase_price(self):
        self._set_product_variant_field("last_purchase_price")

    def _search_last_purchase_price(self, operator, value):
        return [("product_variant_ids.last_purchase_price", operator, value)]

    @api.onchange("list_price")
    def onchange_list_price(self):
        AccountTax = self.env["account.tax"]
        list_price = AccountTax._fix_tax_included_price_company(
            self.list_price, self.taxes_id, AccountTax, self.company_id
        )
        if self.last_purchase_price:
            trade_markup = (list_price - self.last_purchase_price) / self.last_purchase_price * 100
            self.trade_markup = trade_markup

    @api.onchange("last_purchase_price", "trade_markup")
    def onchange_last_purchase_price(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        change_list_price = safe_eval(get_param("purchase.update_list_price", "False"))
        if not change_list_price:
            return
        AccountTax = self.env["account.tax"]

        currency = self.env.user.company_id.currency_id
        company = self.env.user.company_id
        date = self.env.context.get("date") or fields.Date.today()

        for product in self:
            if product.trade_markup:
                if not product.last_purchase_price:
                    product.last_purchase_price = product.standard_price
                if not product.trade_markup:
                    list_price = AccountTax._fix_tax_included_price_company(
                        product.list_price,
                        product.taxes_id,
                        AccountTax,
                        product.company_id,
                    )
                    if product.last_purchase_price:
                        trade_markup = (list_price - product.last_purchase_price) / product.last_purchase_price * 100
                        product.trade_markup = trade_markup
                list_price = product.last_purchase_price * (1 + product.trade_markup / 100)
                if any(tax.price_include for tax in product.taxes_id):
                    list_price = product.taxes_id.compute_all(list_price, quantity=1, handle_price_include=False)[
                        "total_included"
                    ]

                list_price = currency._convert(list_price, product.currency_id, company, date)
                list_price_round = safe_eval(get_param("sale.list_price_round", "2"))
                product.list_price = round(list_price, list_price_round)


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    def update_last_purchase_price(self):
        date = self.env.context.get("date") or fields.Date.today()
        for item in self:
            from_uom = item.product_uom_id or item.product_tmpl_id.uom_id
            to_uom = item.product_tmpl_id.uom_id
            if not from_uom or not to_uom:
                raise UserError(
                    self.env._("You cannot update the supplier price here. Please edit the supplier info separately")
                )
            price = from_uom._compute_price(item.price, to_uom)

            company = item.company_id or self.env.company
            if item.currency_id:
                to_currency = company.currency_id
                price = item.currency_id._convert(price, to_currency, company, date)
            if price:
                if item.product_id:
                    item.product_id.with_company(company).last_purchase_price = price
                    item.product_id.with_company(company).onchange_last_purchase_price()
                else:
                    item.product_tmpl_id.with_company(company).last_purchase_price = price
                    item.product_tmpl_id.with_company(company).onchange_last_purchase_price()

    def write(self, vals):
        res = super().write(vals)
        if "price" in vals:
            if not self.env.context.get("from_po_confirmation"):
                self.update_last_purchase_price()
        return res

    def create(self, vals_list):
        res = super().create(vals_list)
        if not self.env.context.get("from_po_confirmation"):
            res.update_last_purchase_price()
        return res
