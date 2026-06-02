# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _search_build_domain(self, domain_list, search, fields, extra=None):
        # Drop search terms shorter than the configured minimum length, but only
        # when at least one usable term remains. Short terms (1-2 chars) cannot
        # use the GIN trigram indexes (pg_trgm needs >= 3 chars), so they force
        # sequential scans on product.product / product.alternative while adding
        # almost no selectivity. If every term is short, the search is kept
        # intact to preserve correctness over speed.
        if search:
            min_len = int(self.env["ir.config_parameter"].sudo().get_param("website_search.min_term_length", 3))
            terms = search.split(" ")
            long_terms = [term for term in terms if len(term) >= min_len]
            if long_terms and len(long_terms) != len(terms):
                search = " ".join(long_terms)
        return super()._search_build_domain(domain_list, search, fields, extra=extra)

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        fetch_fields += ["default_code", "display_name"]

        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)

        for _product, data in zip(self, results_data, strict=False):
            if data.get("default_code"):
                data["name"] = "[{}] {}".format(data["default_code"], data["name"])

        return results_data
