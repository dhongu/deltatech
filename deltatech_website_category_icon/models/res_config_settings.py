# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    category_icon_inherit = fields.Boolean(related="website_id.category_icon_inherit", readonly=False)
