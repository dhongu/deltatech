from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    cashier_can_close = fields.Boolean(
        string="Cashiers Close the Register",
        default=True,
        help="With 'Log in with Employees', employees with basic rights can close the register. "
        "The other manager rights stay with the managers, and a cash difference above the "
        "authorized amount still needs a manager.",
    )
