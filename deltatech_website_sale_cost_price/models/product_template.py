# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.http import request
from odoo.tools import float_compare


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_cost_price_for_comparison(self, product_or_template, website, date=None):
        if not date:
            date = fields.Date.context_today(self)
        cost_price = product_or_template.sudo().standard_price

        # Check if cost price should include tax or not
        # and if the website price (res['price']) is with or without tax
        # website.show_line_subtotals_tax_selection is 'tax_excluded' or 'tax_included'
        website_tax_included = website.show_line_subtotals_tax_selection == "tax_included"
        cost_tax_included = website.cost_price_include_tax

        if website_tax_included != cost_tax_included:
            # We need to adjust cost_price to match website_tax_included
            taxes = product_or_template.taxes_id.filtered(lambda t: t.company_id == website.company_id)
            # In Odoo 19 the website no longer stores ``fiscal_position_id``; the current
            # fiscal position is resolved per session/request.
            fiscal_position = request.fiscal_position if request else None
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

    def _get_additionnal_combination_info(self, product_or_template, quantity, uom, date, website):
        res = super()._get_additionnal_combination_info(product_or_template, quantity, uom, date, website)

        if website.prevent_zero_price_sale:
            price = res["price"]
            cost_price = self.sudo()._get_cost_price_for_comparison(product_or_template, website, date)

            if float_compare(price, cost_price, precision_rounding=website.currency_id.rounding) < 0:
                res["prevent_zero_price_sale"] = True

        return res

    def _website_show_quick_add(self):
        res = super()._website_show_quick_add()
        if res:
            website = self.env["website"].get_current_website()
            if website.prevent_zero_price_sale:
                price = self._get_contextual_price()
                cost_price = self.sudo()._get_cost_price_for_comparison(self, website)
                if float_compare(price, cost_price, precision_rounding=website.currency_id.rounding) < 0:
                    return False
        return res
