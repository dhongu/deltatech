# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    # def _compute_enable_download(self):
    #     res = super()._compute_enable_download()
    #
    #     for wizard in self:
    #         if wizard.enable_download and wizard.mode == 'invoice_single':
    #             for move in wizard.move_ids:
    #                 if move.partner_id.print_green_invoice:
    #                     wizard.enable_download = False
    #                     break
    #     return res

    def _compute_checkbox_download(self):
        res = super()._compute_checkbox_download()
        for wizard in self:
            if wizard.checkbox_download and wizard.mode == "invoice_single":
                for move in wizard.move_ids:
                    if move.partner_id.print_green_invoice:
                        wizard.checkbox_download = False
                        break
        return res
