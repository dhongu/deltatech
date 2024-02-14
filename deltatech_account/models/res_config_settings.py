# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    use_anglo_saxon = fields.Boolean(
        string="Anglo-Saxon Accounting", related="company_id.anglo_saxon_accounting", readonly=False
    )

    # campl pt transfer_account_id exsta
