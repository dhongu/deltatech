# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # Avansuri de trezorerie
    account_cash_advances_id = fields.Many2one("account.account", string="Cash advances")
