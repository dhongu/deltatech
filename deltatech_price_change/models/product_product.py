# ©  2025 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.tools.safe_eval import safe_eval


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_price_change_items(self):
        self.ensure_one()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        domain = [("product_template_id", "=", self.id), ("price_change_id.state", "=", "done")]
        public_pricelist_id = safe_eval(get_param("price_change.public_pricelist_id", "False"))
        if public_pricelist_id:
            domain += [("pricelist_id", "=", public_pricelist_id)]
        price_changes = self.env["product.price.change.line"].search(domain)
        if not price_changes:
            # get price changes from template
            price_changes = self.product_tmpl_id.get_price_change_items()
        return price_changes
