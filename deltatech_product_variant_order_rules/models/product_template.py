from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def open_order_rules_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Order Rules Details",
            "res_model": "order.rules.details.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,  # Pass the current product.template ID
                "active_model": "product.template",
            },
        }
