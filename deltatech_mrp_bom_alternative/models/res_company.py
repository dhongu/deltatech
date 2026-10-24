from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    mrp_alternative_partial = fields.Boolean(
        string="Partial Substitution",
        default=True,
        help="Allow a component to be split between the original product and one or more alternatives. "
        "When unchecked, an alternative is used only if it covers the whole shortage.",
    )
    mrp_alternative_on_assign = fields.Boolean(
        string="Substitute on Availability Check",
        default=True,
        help="Run the automatic substitution again when the availability of a manufacturing order is checked, "
        "not only when the order is confirmed.",
    )
