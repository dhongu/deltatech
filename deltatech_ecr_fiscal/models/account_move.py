# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "deltatech.ecr.fiscal.mixin"]
