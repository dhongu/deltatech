# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    purchase_keep_discount = fields.Boolean(
        "Keep discount from purchase line",
        related="company_id.purchase_keep_discount",
        readonly=False,
    )
