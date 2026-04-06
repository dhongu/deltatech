# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_manufacturer = fields.Boolean(string="Is manufacturer")
