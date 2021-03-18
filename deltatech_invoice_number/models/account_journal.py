# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    journal_sequence_id = fields.Many2one("ir.sequence", string="Sequence", copy=False)
