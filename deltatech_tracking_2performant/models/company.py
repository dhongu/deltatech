# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    campaign_unique_2p = fields.Char(string="2Performant Campaign Unique")
    confirm_2p = fields.Char(string="2Performant Confirm")
