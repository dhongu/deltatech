# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountModifier(models.Model):
    _name = "account.modifier"
    _description = "Account Modifier"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Short code used in account mapping rules")
