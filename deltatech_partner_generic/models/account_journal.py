# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    restriction = fields.Boolean(
        string="Generic Restriction",
        help="This journal is not proposed when registering a payment for the generic partner.",
    )
