# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.http import request
from odoo.tools import float_compare


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_cost_price_for_comparison(self, product_or_template, website, date=None, fiscal_position=None):
        if not date:
            date = fields.Date.context_today(self)
        cost_price = product_or_template.sudo().standard_price

        # Check if cost price should include tax or not
        # and if the website price (res['price']) is with or without tax.
        # In Odoo 20 the displayed price follows ``website.tax_display``
        # (the pricelist may override ``show_line_subtotals_tax_selection``).
        website_tax_included = website.tax_display == "tax_included"
        cost_tax_included = website.cost_price_include_tax

        if website_tax_included != cost_tax_included:
            # We need to adjust cost_price to match website_tax_included
            taxes = product_or_template.taxes_id.filtered(lambda t: t.company_id == website.company_id)
            # The current fiscal position is resolved per session/request; in Odoo 20 it is
            # also passed explicitly to ``_get_additional_combination_info``.
            if fiscal_position is None:
                fiscal_position = getattr(request, "fiscal_position", None) if request else None
            if fiscal_position:
                taxes = fiscal_position.map_tax(taxes)

            if website_tax_included:
                # Add taxes to cost_price
                cost_price = taxes.compute_all(
                    cost_price, product=product_or_template, partner=self.env.user.partner_id
                )["total_included"]
            else:
                # Remove taxes from cost_price (if it was included)
                # This case is when cost_price_include_tax is True but website is tax_excluded
                cost_price = taxes.compute_all(
                    cost_price, product=product_or_template, partner=self.env.user.partner_id
                )["total_excluded"]

        if website.currency_id != product_or_template.currency_id:
            cost_price = product_or_template.currency_id._convert(
                cost_price, website.currency_id, website.company_id, date
            )

        if website.cost_price_margin_percentage:
            cost_price = cost_price * (1 + website.cost_price_margin_percentage / 100.0)

        return cost_price

    def _get_additional_combination_info(
        self, product_or_template, quantity, uom, website, pricelist, fiscal_position, **kwargs
    ):
        res = super()._get_additional_combination_info(
            product_or_template, quantity, uom, website, pricelist, fiscal_position, **kwargs
        )

        if website._is_cost_price_protection_enabled() and not res.get("prevent_sale"):
            price = res["price"]
            cost_price = self.sudo()._get_cost_price_for_comparison(
                product_or_template, website, fiscal_position=fiscal_position
            )

            if float_compare(price, cost_price, precision_rounding=website.currency_id.rounding) < 0:
                # 19.0: ``prevent_zero_price_sale`` hid both the price and the "Add to Cart"
                # button; in 20.0 these are ``prevent_sale`` and ``hide_price``.
                res["prevent_sale"] = True
                res["hide_price"] = True

        return res

    def _website_show_quick_add(self, product=None):
        res = super()._website_show_quick_add(product=product)
        if res:
            website = self.env.website
            if website and website._is_cost_price_protection_enabled():
                product_or_template = product or self
                price = product_or_template._get_contextual_price()
                cost_price = self.sudo()._get_cost_price_for_comparison(product_or_template, website)
                if float_compare(price, cost_price, precision_rounding=website.currency_id.rounding) < 0:
                    return False
        return res
