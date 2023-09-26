# ©  2015-2020 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


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
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )
        if combination_info["product_id"]:
            product_id = combination_info["product_id"]
            product = self.env["product.product"].browse(product_id)
        else:
            product = self
        if pricelist:
            public_pricelist = self.env["product.pricelist"].search([("selectable", "=", True)])
            if len(public_pricelist) > 1:
                public_pricelist = public_pricelist[0]
            list_price = public_pricelist.get_product_price(product, add_qty, False)
            if pricelist.currency_id != public_pricelist.currency_id:
                list_price = public_pricelist.currency_id._convert(
                    from_amount=list_price,
                    to_currency=pricelist.currency_id,
                    company=self.company_id or self.env.company,
                    date=fields.Date.today(),
                    round=True,
                )
            price = combination_info["price"]
            has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1

            combination_info.update(
                price=price,
                list_price=list_price,
                has_discounted_price=has_discounted_price,
            )
        return combination_info
