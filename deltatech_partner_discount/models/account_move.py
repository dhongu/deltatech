# © 2021 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_discount = fields.Float(related="commercial_partner_id.discount")
