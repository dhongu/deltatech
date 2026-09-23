# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.fields import Domain
from odoo.tools.sql import SQL

# What is typed into a product field is split on whitespace and every token has to
# match, so "apple ga" finds "Apples (Gala, 70/75 mm)". Past this count the input
# has stopped being a search — it is a line pasted by mistake — and every extra
# token costs another subquery, so we let core answer it alone.
MAX_SEARCH_TOKENS = 5

LIKE_OPERATORS = ("=", "like", "ilike", "=like", "=ilike")


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _attribute_search_domain(self, operator, value):
        """Domain matching a variant on its name, its reference or its attribute values.

        Core looks up the template name, the internal reference and the barcode, but
        never the attribute values — so a variant that differs from its siblings only
        by attribute cannot be found by typing that attribute, which is the only thing
        telling the two apart on screen. Every token is looked up in all three places
        and the tokens are ANDed, which is what makes a query mixing them ("apple gala
        70") work: no single field holds all three words.

        Returns ``Domain.FALSE`` when the search does not apply, so the caller can skip
        the query altogether instead of running one that cannot match.
        """
        if operator not in LIKE_OPERATORS:
            # Negative and non-textual operators are left to core. Excluding variants
            # whose attribute value does not match is a different question from finding
            # the ones whose value does, and answering it here would silently narrow
            # searches this module is not meant to touch.
            return Domain.FALSE
        tokens = (value or "").split()
        if not tokens or len(tokens) > MAX_SEARCH_TOKENS:
            return Domain.FALSE

        if len(tokens) == 1:
            # Core already looked the word up in the name and the reference, so the
            # only thing left to add is the attribute values — and on their own they
            # are a chain of indexed lookups over three small tables. Re-ORing the
            # name back in here would be free of any new result and would turn that
            # into a full scan of the variants joined to the templates, because an
            # `ilike` on a translated name cannot use an index. Measured on 20.000
            # variants: 1 ms this way, 19 ms the other.
            return Domain(
                "product_template_attribute_value_ids", "any", self._searchable_value_domain(operator, tokens[0])
            )

        # With several words no single field can hold them all, so this is the part
        # core cannot answer and the scan is the price of answering it. It runs only
        # after core came back short, and the token cap above bounds it.
        domain = Domain.TRUE
        for token in tokens:
            domain &= (
                Domain("name", operator, token)
                | Domain("default_code", operator, token)
                | Domain(
                    # `product_template_attribute_value_ids`, not the `..._variant_...`
                    # one: the latter drops attribute lines that carry a single value,
                    # because those do not tell the variants of a template apart. They
                    # do tell one template from another, though — a product whose only
                    # variety is Idared is still an Idared — and a search that finds it
                    # on one template but not on the other is a hole nobody can explain.
                    "product_template_attribute_value_ids",
                    "any",
                    self._searchable_value_domain(operator, token),
                )
            )
        return domain

    @api.model
    def _searchable_value_domain(self, operator, token):
        """Domain on `product.template.attribute.value` matching one typed word."""
        return Domain("attribute_id.search_ok", "=", True) & Domain("name", operator, token)

    @api.model
    def _search_display_name(self, operator, value):
        # The path taken by search views, by `search([('display_name', 'ilike', ...)])`
        # and by import matching. Core builds a UNION of one subquery per place it
        # looks; the attribute lookup is added as one more branch of it.
        domain = super()._search_display_name(operator, value)
        attribute_domain = self._attribute_search_domain(operator, value)
        if attribute_domain.is_false():
            return domain
        self_no_active_test = self.with_context(active_test=False)
        query = SQL(
            "((%s) UNION ALL (%s))",
            self_no_active_test._search(domain).select(),
            self_no_active_test._search(attribute_domain).select(),
        )
        return [("id", "in", query)]

    @api.model
    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        # The path taken by the product field on an order line, and the one the user
        # actually complains about. Core's `name_search` on products is a bespoke
        # implementation that never goes through `_search_display_name` above, so it
        # needs its own hook.
        #
        # Core answers first and we only top up what it left unfilled: when it already
        # returns a full page, the attribute query never runs, so an installed module
        # costs nothing on the searches that worked before it.
        products = super().name_search(name, domain, operator, limit)
        if not name or (limit and len(products) >= limit):
            return products
        attribute_domain = self._attribute_search_domain(operator, name)
        if attribute_domain.is_false():
            return products
        match_domain = (
            Domain(domain or Domain.TRUE)
            & attribute_domain
            & Domain("id", "not in", [product_id for product_id, _label in products])
        )
        found = self.search_fetch(match_domain, ["display_name"], limit=limit and limit - len(products))
        return products + [(product.id, product.display_name) for product in found]
