# © 2021 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    discount = fields.Float("Proposed discount")
