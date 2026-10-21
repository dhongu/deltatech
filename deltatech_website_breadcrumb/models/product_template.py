# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _breadcrumb_category(self):
        """Category shown in the breadcrumb of the product page: the first category of
        the product available on the current website, preferring one shown in the
        category menu (deltatech_website_shop_snippets hides the campaign categories,
        e.g. new products or offers of the month, with tb_menu_hidden, also for their
        subcategories). An empty record when the product has no category."""
        self.ensure_one()
        categories = self.public_categ_ids
        website = self.env["website"].get_current_website()
        available = categories.filtered(lambda category: not category.website_id or category.website_id == website)
        if "tb_menu_hidden" in categories._fields:

            def in_menu(category):
                ancestors = category.browse(int(part) for part in (category.parent_path or "").split("/") if part)
                return not any(ancestors.mapped("tb_menu_hidden"))

            preferred = available.filtered(in_menu)
            if preferred:
                return preferred[:1]
        return (available or categories)[:1]
