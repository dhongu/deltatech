# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1.0,
        uom_id=False,
        only_template=False,
    ):
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            uom_id=uom_id,
            only_template=only_template,
        )
        list_price = combination_info["list_price"]
        website = self.env["website"].get_current_website()
        if website.show_line_subtotals_tax_selection != "tax_excluded":
            # list_price is the displayed gross price, whatever the tax price_include setting:
            # remove the taxes as if they were all included in the price.
            taxes = combination_info.get("taxes", self.taxes_id)
            res = taxes.with_context(force_price_include=True).compute_all(
                list_price, currency=combination_info.get("currency"), product=self
            )
            list_price = res["total_excluded"]
        combination_info["list_price_without_tax"] = list_price

        return combination_info
