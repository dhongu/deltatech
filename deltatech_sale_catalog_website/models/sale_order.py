# ©  2024 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_add_from_catalog(self):
        # Scope the customization to the Sales catalog only: swap the shared
        # catalog kanban/search views for our own so the Purchase catalog keeps
        # the standard internal categories and image behaviour.
        action = super().action_add_from_catalog()
        kanban_view = self.env.ref("deltatech_sale_catalog_website.product_view_kanban_catalog_website")
        search_view = self.env.ref("deltatech_sale_catalog_website.product_view_search_catalog_website")
        action["views"] = [(kanban_view.id, "kanban"), (False, "form")]
        action["search_view_id"] = [search_view.id, "search"]
        return action
