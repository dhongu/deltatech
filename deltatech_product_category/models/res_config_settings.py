# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

SHARED_CATEGORIES = (
    "product.product_category_all",
    "product.product_category_goods",
    "product.product_category_expenses",
    "product.product_category_services",
)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    company_share_product_category = fields.Boolean(
        "Share product category to all companies",
        help="Share your product category to all companies defined in your instance.\n"
        " * Checked : Product category are visible for every company, even if a company is defined on the partner.\n"
        " * Unchecked : Each company can see only its product category (product category where company is defined). "
        "Product category not related to a company are visible for all companies.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        category_rule = self.env.ref("deltatech_product_category.product_category_comp_rule")
        res.update(
            company_share_product_category=not bool(category_rule.active),
        )

        return res

    def set_values(self):
        res = super().set_values()
        category_rule = self.env.ref("deltatech_product_category.product_category_comp_rule")
        category_rule.write({"active": not bool(self.company_share_product_category)})
        # the standard categories stay shared: "All" (databases migrated from 18.0)
        # and "Goods" / "Expenses" / "Services" (new in 19.0)
        for xmlid in SHARED_CATEGORIES:
            category = self.env.ref(xmlid, raise_if_not_found=False)
            if category and category.company_id:
                category.write({"company_id": False})
        return res
