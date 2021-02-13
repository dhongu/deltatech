# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def view_rate(self):
        action = self.env.ref("deltatech_payment_term.action_account_moves_sale").read()[0]
        action["domain"] = "[('partner_id','='," + str(self.id) + " )]"
        return action
