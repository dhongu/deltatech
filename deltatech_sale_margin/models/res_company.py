# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_margin_check_mode = fields.Selection(
        [
            ("block", "Block the sale"),
            ("warn", "Warn only"),
            ("off", "No check"),
        ],
        string="Selling below cost",
        default="block",
        required=True,
        help="How the system reacts when a sale order line falls below the "
        "purchase price or below the margin limit.\n\n"
        "• Block the sale: the order cannot be confirmed and the price cannot be "
        "saved (unless the user belongs to the bypass groups). This is the "
        "historical behaviour and stays the default.\n"
        "• Warn only: nothing is ever blocked. The line is flagged, the order "
        "shows a banner, and confirming it leaves a single note in the chatter. "
        "Use this when selling below cost is a normal part of the business "
        "(perishable goods, stock clearance, commercial gestures) and the point "
        "is to make it visible, not to prevent it.\n"
        "• No check: no flag, no banner, no block.",
    )
