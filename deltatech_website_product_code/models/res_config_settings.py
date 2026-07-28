# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # A boolean is safe to store through `config_parameter`: core writes False
    # by deleting the parameter, and the search reads a missing parameter as
    # False too. Numeric settings would need explicit get/set, since a zero is
    # also stored as False and would silently restore the default.
    website_search_exact_phrase = fields.Boolean(
        string="Search The Whole Term",
        config_parameter="website_search.exact_phrase",
        help="Match the search term as a single string instead of splitting it on spaces. "
        "Enable it when product codes contain spaces, so that searching '352 030 15 97' returns "
        "the product having that code instead of every product containing '352', '030', '15' or "
        "'97'. When no product matches the whole term, the regular search is used.",
    )
