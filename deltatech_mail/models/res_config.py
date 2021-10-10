# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    use_company_email = fields.Boolean(string="Use Company Email", config_parameter="mail.use_company_email")
