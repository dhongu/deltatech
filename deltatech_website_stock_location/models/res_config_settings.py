# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_location_id = fields.Many2one(
        "stock.location",
        related="website_id.location_id",
        domain="[('company_id', '=', website_company_id)]",
        readonly=False,
    )
