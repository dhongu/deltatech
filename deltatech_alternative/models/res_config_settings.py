# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    alternative_search = fields.Boolean(string="Alternative search", config_parameter="alternative.search_name")
    catalog_search = fields.Boolean(string="Catalog search", config_parameter="alternative.search_catalog")
