# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):

        if self.env.context.get("website_id"):
            current_website = self.env["website"].get_current_website()
            if not pricelist:
                pricelist = current_website.get_current_pricelist()
            discount_policy = pricelist.discount_policy
            pricelist.discount_policy = "without_discount"

        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        if self.env.context.get("website_id"):
            pricelist.discount_policy = discount_policy

        # if self.env.context.get("website_id"):
        #     price = combination_info["price"]
        #
        #     list_price = combination_info.get("price_without_discount", combination_info["price"])
        #
        #     has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1
        #
        #     combination_info.update(
        #         price=price,
        #         list_price=list_price,
        #         has_discounted_price=has_discounted_price,
        #     )
        return combination_info
