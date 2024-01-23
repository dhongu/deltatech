# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    stock_valuation = fields.Boolean(string="Stock Valuation")
