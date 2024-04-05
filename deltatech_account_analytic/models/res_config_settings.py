# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    can_split_analytic = fields.Boolean(related="company_id.can_split_analytic")
    split_sale_analytic = fields.Boolean(related="company_id.split_sale_analytic", readonly=False)
