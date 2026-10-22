# ©  2025 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        if "list_price" not in vals or self.env.context.get("skip_price_change_log"):
            return super().write(vals)
        old_prices = {template.id: template.list_price for template in self}
        res = super().write(vals)
        self.env["product.price.change.log"]._log_list_price_change(self, old_prices)
        return res

    def action_view_price_change_log(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_price_change.action_price_change_log")
        action["domain"] = [("product_tmpl_id", "=", self.id)]
        return action

    def get_price_change_items(self):
        self.ensure_one()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        domain = [("product_template_id", "=", self.id), ("price_change_id.state", "=", "done")]
        public_pricelist_id = safe_eval(get_param("price_change.public_pricelist_id", "False"))
        if public_pricelist_id:
            domain += [("pricelist_id", "=", public_pricelist_id)]
        return self.env["product.price.change.line"].search(domain)
