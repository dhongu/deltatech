# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re

from odoo import api, models
from odoo.osv import expression
from odoo.tools import escape_psql, str2bool

_CODE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-_./]{2,}$")


def _looks_like_code(term):
    return bool(_CODE_RE.match(term)) and any(ch.isdigit() for ch in term)


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

    @api.model
    def _search_fetch(self, search_detail, search, limit, order):
        # Codes may contain spaces (OEM part numbers such as "352 030 15 97").
        # The default search splits the term on spaces and matches each piece
        # separately, so searching for one such code returns every product
        # containing "352" or "030" or "15" or "97" - pages of noise with the
        # wanted product buried in the middle. When exact-phrase search is on,
        # the whole term is matched as one string first, and only the per-term
        # AND search of the mixin is used as a fallback.
        phrase = " ".join((search or "").split())
        exact_phrase = " " in phrase and self._exact_phrase_search_enabled()
        if exact_phrase:
            results, count = self._search_fetch_exact_phrase(search_detail, phrase, limit, order)
            if count:
                return results, count
        # When someone pastes a list of product codes into the shop search box,
        # the default domain ORs every term against every search field in one
        # WHERE clause. Some fields are plain columns (trigram-indexable) and
        # some are relational (product_variant_ids.*, alternative_ids.*, resolved
        # via subqueries); PostgreSQL can't build one combined bitmap plan across
        # a mix of column and subquery conditions joined by OR, so with
        # ORDER BY website_sequence LIMIT N it falls back to scanning the table
        # in that order and evaluating the whole filter per row - measured at
        # ~10s for 14 pasted codes against ~123k products (EXPLAIN ANALYZE).
        # Searching one field at a time instead (still ORing all terms within
        # each field) lets every branch use its own index; ~500x faster on the
        # same data, same results (still ORed/deduped across all fields).
        # This must not run in exact-phrase mode: there, a term containing
        # spaces is one code, not a list of codes, so ORing its groups produces
        # exactly the noise that mode exists to remove. A code such as
        # "999 888 777 666" would otherwise match every product containing any
        # of the four groups - measured at 472 results on a 10k-product
        # catalogue, where the per-term AND fallback returns none.
        terms = [t for t in (search or "").split(" ") if t.strip()]
        min_terms = self._multi_code_min_terms()
        if (
            not exact_phrase
            and min_terms
            and len(terms) >= min_terms
            and not search_detail.get("search_extra")
            and all(_looks_like_code(t) for t in terms)
        ):
            return self._search_fetch_multi_code(search_detail, terms, limit, order)
        return super()._search_fetch(search_detail, search, limit, order)

    def _exact_phrase_search_enabled(self):
        param = self.env["ir.config_parameter"].sudo().get_param("website_search.exact_phrase", "False")
        return str2bool(param, False)

    def _search_fetch_exact_phrase(self, search_detail, phrase, limit, order):
        """Search the whole term as a single string, in any of the search fields."""
        base_domain = search_detail["base_domain"]
        model = self.sudo() if search_detail.get("requires_sudo") else self

        subdomains = [[(field_name, "ilike", escape_psql(phrase))] for field_name in search_detail["search_fields"]]
        extra = search_detail.get("search_extra")
        if extra:
            subdomains.append(extra(self.env, phrase))
        domain = expression.AND(base_domain + [expression.OR(subdomains)])

        results = model.search(domain, limit=limit, order=search_detail.get("order", order))
        count = model.search_count(domain) if limit and limit == len(results) else len(results)
        return results, count

    def _multi_code_min_terms(self):
        # False/0/empty/anything non-numeric disables the fast path, falling
        # back to the legacy behavior - int("False") would otherwise raise.
        param = self.env["ir.config_parameter"].sudo().get_param("website_search.multi_code_min_terms", "4")
        try:
            return int(param)
        except (ValueError, TypeError):
            return 0

    def _search_fetch_multi_code(self, search_detail, terms, limit, order):
        base_domain = search_detail["base_domain"]
        search_fields = search_detail["search_fields"]
        model = self.sudo() if search_detail.get("requires_sudo") else self
        branch_limit = max(limit * 20, 500)

        all_ids = set()
        for field_name in search_fields:
            term_domain = expression.OR([[(field_name, "ilike", escape_psql(term))] for term in terms])
            branch_domain = expression.AND(base_domain + [term_domain])
            all_ids.update(model.search(branch_domain, limit=branch_limit, order="id").ids)

        if not all_ids:
            return model.browse(), 0

        final_domain = [("id", "in", list(all_ids))]
        results = model.search(final_domain, limit=limit, order=search_detail.get("order", order))
        count = model.search_count(final_domain) if limit and limit == len(results) else len(results)
        return results, count

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        fetch_fields += ["default_code", "display_name"]

        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)

        for _product, data in zip(self, results_data, strict=False):
            if data.get("default_code"):
                data["name"] = "[{}] {}".format(data["default_code"], data["name"])

        return results_data
