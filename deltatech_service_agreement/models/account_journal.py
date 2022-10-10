# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    service_invoice = fields.Boolean(string="Service Invoice")
