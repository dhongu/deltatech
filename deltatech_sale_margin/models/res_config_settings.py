# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # These parameters existed before but were reachable only through System
    # Parameters, so in practice nobody configured them. Exposing them next to
    # the reaction mode is what makes the whole feature usable by a consultant.
    sale_margin_check_mode = fields.Selection(
        related="company_id.sale_margin_check_mode",
        readonly=False,
    )
    sale_margin_limit = fields.Float(
        string="Margin limit (%)",
        config_parameter="sale.margin_limit",
        help="Margin percentage below which a sale order line is reported.\n"
        "0 (default) reports only negative margins, i.e. strictly below the "
        "purchase price. A negative value tolerates a loss of up to that "
        "percentage without reporting it — useful when the warning would "
        "otherwise appear on so many orders that nobody reads it any more. "
        "A positive value also reports thin but positive margins.",
    )
    sale_margin_limit_check_validate = fields.Boolean(
        string="Check margin on confirmation only",
        config_parameter="sale.margin_limit_check_validate",
        help="Check the price only when the order is confirmed, instead of on every change of a line.",
    )
