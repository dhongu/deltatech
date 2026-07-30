# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_show_reset_to_draft_button(self):
        res = super()._compute_show_reset_to_draft_button()
        access = self.env.user.has_group("deltatech_invoice_to_draft.group_reset_to_draft_account_move")
        for move in self:
            move.show_reset_to_draft_button = move.show_reset_to_draft_button and access
        return res

    def button_draft_cancel(self):
        self.button_draft()
        self.button_cancel()
