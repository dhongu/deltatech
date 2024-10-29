# ©  2008-2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    provider_id = fields.Many2one("payment.provider")
