# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def action_pricelist_bulk_add(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("deltatech_pricelist_bulk.action_pricelist_bulk_add")
        action["context"] = {"default_pricelist_id": self.id}
        return action

    def action_pricelist_bulk_formula(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("deltatech_pricelist_bulk.action_pricelist_bulk_formula")
        action["context"] = {"default_item_ids": self.item_ids.ids}
        return action


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _get_bulk_action(self):
        """Window action listing these rules, opened after a bulk change."""
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Price Rules"),
            "res_model": "product.pricelist.item",
            "view_mode": "list,form",
            "views": [(False, "list"), (False, "form")],
            "domain": [("id", "in", self.ids)],
        }
