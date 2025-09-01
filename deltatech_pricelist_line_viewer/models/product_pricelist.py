# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def action_view_lines(self):
        self.ensure_one()
        tree_view_id = self.env.ref("deltatech_pricelist_line_viewer.product_pricelist_lines_view").id
        form_view_id = self.env.ref("product.product_pricelist_item_form_view").id
        search_view_id = self.env.ref("product.product_pricelist_item_view_search").id

        return {
            "type": "ir.actions.act_window",
            "name": "Pricelist Items",
            "res_model": "product.pricelist.item",
            "view_mode": "tree,form",
            "views": [
                (tree_view_id, "tree"),
                (form_view_id, "form"),
            ],
            "search_view_id": search_view_id,
            "domain": [("pricelist_id", "=", self.id)],
            "context": {"default_pricelist_id": self.id},
        }
