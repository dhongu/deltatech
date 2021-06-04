# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    generic_partner_id = fields.Many2one("res.partner", "Generic Partner", config_parameter="sale.partner_generic_id")
