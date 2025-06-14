# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    account_modifier_id = fields.Many2one("account.modifier", string="Account Modifier")
