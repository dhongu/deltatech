from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    lock_price_for_managers = fields.Boolean(
        string="Lock Price for Managers",
        help="Nobody can change the product price on the order, not even the POS managers. "
        "A wrong price is corrected on the product form and reaches the register from there.",
    )
