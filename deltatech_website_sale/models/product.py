# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # #008a00!important  - in stoc
    # #c45500!important  - la comanda  Usually dispatched within 4 to 5 days.

    # exista  inventory_availability cu care trebuie sa existe o relatie
    # is_qty_available = fields.Selection(
    #     [("stock", "In Stock"), ("provider", "In provider stock"), ("order", "At Order")], compute="_compute_available"
    # )
    # at_order = fields.Boolean(string="Available at order")

    inventory_availability = fields.Selection(default="threshold")
    available_threshold = fields.Float(default=1.0)

    published_on_website = fields.Boolean(related="is_published", readonly=False, string="Published")

    @api.multi
    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):

        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        if self.env.context.get("website_id"):
            current_website = self.env["website"].get_current_website()
            if not pricelist:
                pricelist = current_website.get_current_pricelist()

            price = combination_info["price"]

            list_price = combination_info.get("web_list_price", combination_info["price"])

            has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1

            combination_info.update(
                price=price,
                list_price=list_price,
                has_discounted_price=has_discounted_price,
            )
        return combination_info

    # @api.multi
    # @api.depends("qty_available", "at_order")
    # def _compute_available(self):
    #     res = {}
    #     for product in self:
    #         if product.sudo().qty_available > 0 or product.sudo().inventory_availability == "always":
    #             product.is_qty_available = "stock"
    #         else:
    #             if product.at_order:
    #                 product.is_qty_available = "order"
    #             else:
    #                 product.is_qty_available = "provider"
    #     return res
