# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    # Deprecated: bridge to the standard GLN of `account_add_gln`, kept so that
    # code and data still writing or reading `gln` keep working. No own column.
    gln = fields.Char(
        string="GLN (deprecated)",
        related="global_location_number",
        readonly=False,
        help="Deprecated, use the standard Global Location Number field.",
    )
