# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def view_rate(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_payment_term.action_account_moves_sale")
        # open (not reconciled) customer rates of the partner, posted invoices only
        action["domain"] = [
            ("partner_id", "=", self.id),
            ("display_type", "=", "payment_term"),
            ("account_type", "=", "asset_receivable"),
            ("parent_state", "=", "posted"),
            ("reconciled", "=", False),
        ]
        return action
