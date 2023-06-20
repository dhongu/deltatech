# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    refund_journal_id = fields.Many2one("account.journal", string="Refund journal")
