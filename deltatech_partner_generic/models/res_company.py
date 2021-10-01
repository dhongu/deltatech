# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    generic_partner_id = fields.Many2one("res.partner", "Generic Partner")
