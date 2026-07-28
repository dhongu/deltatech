# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models

# Parameter name -> default used when it was never set. These must match the
# defaults read in product.template, otherwise saving the settings page without
# touching anything would change the behaviour of the shop.
INT_PARAMS = {
    "website_search.standalone_code_min_length": ("website_search_standalone_code_min_length", 5),
    "website_search.multi_code_min_terms": ("website_search_multi_code_min_terms", 4),
    "website_search.min_term_length": ("website_search_min_term_length", 3),
}


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_search_exact_phrase = fields.Boolean(
        string="Search The Whole Term",
        config_parameter="website_search.exact_phrase",
        help="Match the search term as a single string instead of splitting it on spaces. "
        "Enable it when product codes contain spaces, so that searching '352 030 15 97' returns "
        "the product having that code instead of every product containing '352', '030', '15' or "
        "'97'. When no product matches the whole term, the regular search is used.",
    )
    # The integers below deliberately avoid `config_parameter`: that mechanism
    # stores a zero as False, which deletes the parameter and therefore restores
    # the default. Zero means "disabled" here, so it has to be written out.
    website_search_standalone_code_min_length = fields.Integer(
        string="Shortest Standalone Code",
        default=5,
        help="Used only while the whole term is searched, to tell a pasted list of complete codes "
        "from the groups of a single code written with spaces. Terms shorter than this are taken "
        "to be groups of one code, so they are never searched separately. Use 0 to accept terms of "
        "any length as codes.",
    )
    website_search_multi_code_min_terms = fields.Integer(
        string="Pasted Code Lists",
        default=4,
        help="Number of code-looking terms pasted together before the search starts looking for "
        "any of them, instead of requiring a single product to match them all. Use 0 to disable.",
    )
    website_search_min_term_length = fields.Integer(
        string="Shortest Search Term",
        default=3,
        help="Terms shorter than this are ignored, since they cannot use the database indexes and "
        "only slow the search down. Kept when every term is shorter than this, so that such a "
        "search still returns its results. Use 0 to keep every term.",
    )

    def get_values(self):
        res = super().get_values()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        for param, (field_name, default) in INT_PARAMS.items():
            try:
                res[field_name] = int(get_param(param, default))
            except (TypeError, ValueError):
                # A non-numeric value (e.g. the legacy "False") disables it.
                res[field_name] = 0
        return res

    def set_values(self):
        res = super().set_values()
        set_param = self.env["ir.config_parameter"].sudo().set_param
        for param, (field_name, _default) in INT_PARAMS.items():
            set_param(param, str(self[field_name]))
        return res
