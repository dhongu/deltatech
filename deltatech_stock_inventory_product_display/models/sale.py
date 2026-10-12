# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_view_products(self):
        action = self.env["ir.actions.actions"]._for_xml_id("product.product_template_action")
        pids = []
        for line in self.order_line:
            if line.product_id:
                pids.append(line.product_id.product_tmpl_id.id)
        action["domain"] = [("id", "in", pids)]
        action["context"] = {
            "display_free_quantity": True,
        }
        return action
