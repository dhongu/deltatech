# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # cred ca jurnalul trebuie sa depinda de codum de compaien
    journal_bf_id = fields.Many2one(
        "account.journal", "Journal Bon Fiscal", domain="[('type', '=', 'sale')]", config_parameter="sale.journal_bf_id"
    )
