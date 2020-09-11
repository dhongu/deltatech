# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    use_anglo_saxon = fields.Boolean(
        string="Anglo-Saxon Accounting", related="company_id.anglo_saxon_accounting", readonly=False
    )

    transfer_account_id = fields.Many2one(
        "account.account",
        string="Transfer Account",
        related="company_id.transfer_account_id",
        readonly=False,
        domain=lambda self: [
            ("reconcile", "=", True),
            ("user_type_id.id", "=", self.env.ref("account.data_account_type_current_assets").id),
        ],
        help="Intermediary account used when moving money from a liquidity account to another",
    )
