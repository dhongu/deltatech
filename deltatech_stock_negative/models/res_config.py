# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    no_negative_stock = fields.Boolean(
        string="No negative stock",
        help="Allows you to prohibit negative stock quantities.",
    )
    no_negative_stock_pos_bypass = fields.Boolean(
        string="Allow negative stock from Point of Sale",
        default=True,
        help="At a cash register the goods leave the shop as the receipt is paid, "
        "so refusing to validate its delivery does not keep the stock on the shelf - "
        "it only stops the system from recording what already happened. Leave this on "
        "to let a Point of Sale receipt go through even when it takes the location "
        "below zero; the bypass is logged, and the deviation stays visible as negative "
        "stock to be corrected. Turn it off to apply the no-negative-stock rule to "
        "Point of Sale as well.",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    no_negative_stock = fields.Boolean(
        related="company_id.no_negative_stock",
        string="No negative stock",
        readonly=False,
        help="Allows you to prohibit negative stock quantities.",
    )
    no_negative_stock_pos_bypass = fields.Boolean(
        related="company_id.no_negative_stock_pos_bypass",
        string="Allow negative stock from Point of Sale",
        readonly=False,
        help="Let a Point of Sale receipt validate its delivery even when it takes "
        "the location below zero. The goods have already left the shop.",
    )
