# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools.sql import create_index, index_exists

_logger = logging.getLogger(__name__)


def _ensure_trgm_prerequisites(cr):
    """Ensure pg_trgm and unaccent are installed and unaccent is IMMUTABLE.

    Both extensions are required for the GIN trigram indexes used by the
    website product search. They are commonly absent in CI databases or fresh
    PostgreSQL clusters.
    """
    try:
        with cr.savepoint():
            cr.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        with cr.savepoint():
            cr.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
        with cr.savepoint():
            cr.execute("""
                CREATE OR REPLACE FUNCTION public.unaccent(text)
                RETURNS text LANGUAGE sql IMMUTABLE AS
                $$ SELECT public.unaccent('unaccent', $1) $$
            """)
        return True
    except Exception:
        return False


def _create_trgm_index(cr, indexname, tablename, expression):
    """Create a GIN trigram index on an ``unaccent(...)`` expression.

    The website product search filters with ``unaccent(<col>) ILIKE '%...%'``.
    A plain btree (or a trigram index built on the raw column) cannot serve
    that predicate, so PostgreSQL falls back to a sequential scan. This helper
    builds an index whose expression matches the search exactly.

    If the first attempt fails (unaccent missing or not IMMUTABLE) it tries to
    install the extension and create the IMMUTABLE wrapper, then retries once.
    Only if that also fails does it fall back to logging a warning.
    """
    if index_exists(cr, indexname):
        return
    try:
        with cr.savepoint():
            create_index(cr, indexname, tablename, [expression], method="gin")
    except Exception:
        if _ensure_trgm_prerequisites(cr):
            try:
                with cr.savepoint():
                    create_index(cr, indexname, tablename, [expression], method="gin")
                return
            except Exception:
                _logger.debug("Retry of trigram index %s failed after unaccent setup.", indexname, exc_info=True)
        _logger.warning(
            "Could not create trigram index %s on %s; product search may be "
            "slow. Make sure the 'unaccent' function is declared IMMUTABLE.",
            indexname,
            tablename,
        )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def init(self):
        # Matches the website search predicate `unaccent(default_code) ILIKE`.
        # The `name` field already gets a trigram index from core (index="trigram"),
        # but `default_code` (a stored compute) has none.
        _create_trgm_index(
            self.env.cr,
            "product_template_default_code_unaccent_gin",
            "product_template",
            "unaccent(default_code) gin_trgm_ops",
        )
        return super().init()

    alternative_code = fields.Char(
        string="Alternative Code",
        index=True,
        inverse="_inverse_alternative_code",
        compute="_compute_alternative_code",
        # NOTE: the field-level `unaccent` parameter was removed in Odoo 18.
        # Unaccent is now decided globally per registry (registry.unaccent,
        # based on whether the PostgreSQL `unaccent` function is installed and
        # immutable) and applied unconditionally to every char/text `ilike`.
        # There is no per-field opt-out; passing `unaccent=False` here would be
        # silently ignored. To make a search accent-sensitive, override the
        # relevant `_search`/`name_search` with custom SQL instead.
    )
    alternative_ids = fields.One2many("product.alternative", "product_tmpl_id", string="Alternatives")

    used_for = fields.Char(string="Used For")

    def _inverse_alternative_code(self):
        for product in self:
            if any(a.hide for a in product.alternative_ids):
                continue
            if len(product.alternative_ids) == 1:
                product.alternative_ids.name = product.alternative_code
            if not product.alternative_ids:
                product.alternative_ids = self.env["product.alternative"].create({"name": product.alternative_code})

    @api.depends("alternative_ids")
    def _compute_alternative_code(self):
        for product in self:
            codes = []
            for cod in product.alternative_ids:
                if cod.name and not cod.hide:
                    codes += [cod.name]

            code = "; ".join(codes)
            product.alternative_code = code

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100) -> list[tuple[int, str]]:
        res = super().name_search(name=name, args=args, operator=operator, limit=limit)
        if len(res) >= limit:
            return res
        left = limit - len(res)

        get_param = self.env["ir.config_parameter"].sudo().get_param
        if name and safe_eval(get_param("alternative.search_name", "False")):
            domain = [("name", operator, name)]
            alternatives = self.env["product.alternative"].search(domain, limit=left)
            product_tmpl_ids = alternatives.mapped("product_tmpl_id")
            current_ids = {r[0] for r in res}
            product_tmpl_ids = product_tmpl_ids.filtered(lambda p: p.id not in current_ids and p.active)
            product_tmpl_ids = product_tmpl_ids[:left]
            res += [(p.id, p.display_name) for p in product_tmpl_ids]
        if limit:
            res = res[:limit]
        return res

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if value and safe_eval(get_param("alternative.search_name", "False")):
            alternative_domain = [("alternative_ids.name", operator, value), ("active", "=", True)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.AND([domain, alternative_domain])
            else:
                domain = expression.OR([domain, alternative_domain])
        return domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    def init(self):
        # Matches the website search predicate `unaccent(default_code) ILIKE`.
        _create_trgm_index(
            self.env.cr,
            "product_product_default_code_unaccent_gin",
            "product_product",
            "unaccent(default_code) gin_trgm_ops",
        )
        return super().init()

    # def _name_search nu mai exista in 18.0

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100) -> list[tuple[int, str]]:
        res = super().name_search(name=name, args=args, operator=operator, limit=limit)
        if len(res) >= limit:
            return res
        left = limit - len(res)
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if name and safe_eval(get_param("alternative.search_name", "False")):
            domain = [("name", operator, name)]
            alternatives = self.env["product.alternative"].search(domain, limit=left)
            product_tmpl_ids = alternatives.mapped("product_tmpl_id")

            variants = product_tmpl_ids.mapped("product_variant_ids")
            current_ids = {r[0] for r in res}
            variants = variants.filtered(lambda p: p.id not in current_ids and p.active)
            variants = variants[:left]

            res += [(p.id, p.name) for p in variants]
        if limit:
            res = res[:limit]
        return res

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if value and safe_eval(get_param("alternative.search_name", "False")):
            alternative_domain = [("alternative_ids.name", operator, value), ("active", "=", True)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.AND([domain, alternative_domain])
            else:
                domain = expression.OR([domain, alternative_domain])
        return domain


class ProductAlternative(models.Model):
    _name = "product.alternative"
    _description = "Product alternative"

    name = fields.Char(string="Code", index="btree_not_null")
    sequence = fields.Integer(string="sequence", default=10)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", ondelete="cascade")
    hide = fields.Boolean(string="Hide")

    def init(self):
        # Matches the website search predicate `unaccent(name) ILIKE`.
        # A trigram index on the raw `name` column is NOT used by that filter.
        _create_trgm_index(
            self.env.cr,
            "product_alternative_name_unaccent_gin",
            "product_alternative",
            "unaccent(name) gin_trgm_ops",
        )
        return super().init()

    @api.model
    def split_multi_codes(self):
        import re

        domain = [
            ("name", "!=", False),
            "|",
            "|",
            ("name", "like", ";"),
            ("name", "like", ","),
            ("name", "like", " "),
        ]
        records = self.search(domain, limit=5000)
        for record in records:
            name = (record.name or "").strip()
            if not name:
                continue
            codes = [c for c in re.split(r"[;,\s]+", name) if c]
            if len(codes) > 1:
                record.write({"name": codes[0]})
                new_records = [
                    {
                        "name": code,
                        "product_tmpl_id": record.product_tmpl_id.id or False,
                        "sequence": record.sequence,
                        "hide": record.hide,
                    }
                    for code in codes[1:]
                ]
                self.create(new_records)
