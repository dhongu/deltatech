# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    alternative_search = fields.Boolean(string="Alternative Search", config_parameter="alternative.search_name")
    # catalog_search = fields.Boolean(string="Catalog Search", config_parameter="alternative.search_catalog")
    alternative_limit = fields.Integer(string="Alternative Limit", config_parameter="alternative.limit", default=10)
    alternative_length_min = fields.Integer(string="Mimim Length", config_parameter="alternative.length_min", default=3)
