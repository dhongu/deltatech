# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def show_pallets_status(self):
        pallet_category = self.env["product.category"].search([("pallet", "=", True)])
        pallet_product = self.env["product.product"].search([("categ_id", "in", pallet_category.ids)])

        done_states = self.env["sale.report"]._get_done_states()
        domain = [
            ("partner_id", "=", self.partner_id.id),
            ("product_id", "in", pallet_product.ids),
            ("state", "in", done_states),
        ]

        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_order_report_all")

        action["domain"] = domain
        action["view_mode"] = "pivot"
        action["views"] = [(False, "pivot")]
        action["context"] = {
            "pivot_measures": ["qty_delivered", "qty_invoiced", "price_unit"],
            "pivot_column_groupby": [],
            "pivot_row_groupby": ["product_id", "price_unit"],
            "active_id": self._context.get("active_id"),
            "active_model": "sale.report",
        }
        # action['target'] = 'new'
        return action
