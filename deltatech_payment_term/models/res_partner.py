# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def view_rate(self):
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_payment_term.action_account_moves_sale")
        action["domain"] = "[('partner_id','='," + str(self.id) + " )]"
        return action
