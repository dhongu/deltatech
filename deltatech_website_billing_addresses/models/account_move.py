# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        # Add partner to followers
        res = super().action_post()
        for move in self:
            if move.move_type in ["out_invoice", "out_refund"]:
                # partner of the user who has the invoice address
                user_partner = move.partner_id.access_for_user_id.partner_id
                move.message_subscribe([user_partner.id])
        return res
