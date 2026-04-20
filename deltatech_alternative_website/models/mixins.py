# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class WebsiteSearchableMixin(models.AbstractModel):
    """Mixin to be inherited by all models that need to searchable through website"""

    _inherit = "website.searchable.mixin"

    @api.model
    def _search_build_domain(self, domain_list, search, fields, extra=None):
        if search:
            search = search.strip().split(" ")
            search = " ".join(s.strip() for s in search if s.strip())

        # from odoo.osv import expression
        # from odoo.tools import escape_psql
        # domains = domain_list.copy()
        # if search:
        #     get_param = self.env["ir.config_parameter"].sudo().get_param
        #     alternative_length_min = int(get_param("alternative.length_min", "3"))
        #     fields_to_search_short = [
        #         f for f in fields if f not in ["default_code", "alternative_code", "product_variant_ids.default_code"]
        #     ]
        #     for search_term in search.split(" "):
        #         if len(search_term) < alternative_length_min:
        #             # pentru siruri scurte de caractere nu se cauta in campurile de tip cod
        #             fields_to_search = fields_to_search_short
        #         else:
        #             fields_to_search = fields
        #
        #         subdomains = [[(field, "ilike", escape_psql(search_term))] for field in fields_to_search]
        #         if extra:
        #             subdomains.append(extra(self.env, search_term))
        #         if subdomains:
        #             domains.append(expression.OR(subdomains))
        # return expression.AND(domains)

        return super()._search_build_domain(domain_list, search, fields, extra)
