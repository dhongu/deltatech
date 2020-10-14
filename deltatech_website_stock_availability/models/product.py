# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    inventory_availability = fields.Selection(
        selection_add=[("preorder", "Show inventory below a threshold and allow sales if not enough stock")]
    )

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

        if not self.env.context.get("website_sale_stock_get_quantity"):
            return combination_info

        if combination_info["product_id"]:
            product = self.env["product.product"].sudo().browse(combination_info["product_id"])
            if product.type == "product" and product.inventory_availability in ["preorder"]:
                combination_info["custom_message"] = _("Info stock: in %d days") % (product.sale_delay or 1)

        return combination_info
