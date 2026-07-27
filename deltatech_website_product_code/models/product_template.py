# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.fields import Domain
from odoo.tools import escape_psql, str2bool


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _search_fetch(self, search_detail, search, limit, order):
        # Codes may contain spaces (OEM part numbers such as "352 030 15 97").
        # The default search splits the term on spaces and matches each piece
        # separately, so searching for one such code returns every product
        # containing "352" or "030" or "15" or "97" - pages of noise with the
        # wanted product buried in the middle. When exact-phrase search is on,
        # the whole term is matched as one string first; the per-term search is
        # only used as a fallback, so partial-word searches keep working.
        phrase = " ".join((search or "").split())
        if " " in phrase and self._exact_phrase_search_enabled():
            results, count = self._search_fetch_exact_phrase(search_detail, phrase, limit, order)
            if count:
                return results, count
        return super()._search_fetch(search_detail, search, limit, order)

    def _exact_phrase_search_enabled(self):
        param = self.env["ir.config_parameter"].sudo().get_param("website_search.exact_phrase", "False")
        return str2bool(param, False)

    def _search_fetch_exact_phrase(self, search_detail, phrase, limit, order):
        """Search the whole term as a single string, in any of the search fields."""
        model = self.sudo() if search_detail.get("requires_sudo") else self

        subdomains = [Domain(field_name, "ilike", escape_psql(phrase)) for field_name in search_detail["search_fields"]]
        extra = search_detail.get("search_extra")
        if extra:
            subdomains.append(extra(self.env, phrase))
        domain = Domain.AND(search_detail["base_domain"]) & Domain.OR(subdomains)

        results = model.search(domain, limit=limit, order=search_detail.get("order", order))
        count = model.search_count(domain) if limit and limit == len(results) else len(results)
        return results, count

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        fetch_fields += ["default_code", "display_name"]

        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)

        for _product, data in zip(self, results_data, strict=False):
            if data.get("default_code"):
                data["name"] = "[{}] {}".format(data["default_code"], data["name"])

        return results_data
