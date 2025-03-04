# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    receipt_print = fields.Boolean()  # bon fiscal tiparit

    def print_bf(self):
        pass
