# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging
import re

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

# Only explicit delimiters separate two codes. Whitespace must NOT be treated as
# a delimiter: many OEM part numbers contain spaces ("366 200 05 01"), and
# splitting on them destroys the code and makes the product unsearchable.
_CODE_SEPARATOR_RE = re.compile(r"[;,]+")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alternative_code = fields.Char(
        string="Alternative Code",
        index=True,
        inverse="_inverse_alternative_code",
        compute="_compute_alternative_code",
        # unaccent=False,
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
    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        res = super().name_search(name=name, domain=domain, operator=operator, limit=limit)
        if len(res) >= limit:
            return res
        left = limit - len(res)

        get_param = self.env["ir.config_parameter"].sudo().get_param
        if name and safe_eval(get_param("alternative.search_name", "False")):
            domain = [("name", operator, name)]
            alternatives = self.env["product.alternative"].search(domain, limit=left)
            product_tmpl_ids = alternatives.mapped("product_tmpl_id")
            current_ids = {r[0] for r in res}
            product_tmpl_ids = product_tmpl_ids.filtered(lambda p: p.id not in current_ids)
            product_tmpl_ids = product_tmpl_ids[:left]
            res += [(p.id, p.display_name) for p in product_tmpl_ids]
        if limit:
            res = res[:limit]
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    # def _name_search nu mai exista in 18.0

    @api.model
    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        res = super().name_search(name=name, domain=domain, operator=operator, limit=limit)
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
            variants = variants.filtered(lambda p: p.id not in current_ids)
            variants = variants[:left]

            res += [(p.id, p.name) for p in variants]
        if limit:
            res = res[:limit]
        return res


class ProductAlternative(models.Model):
    _name = "product.alternative"
    _description = "Product alternative"

    name = fields.Char(string="Code", index="btree_not_null")
    sequence = fields.Integer(string="sequence", default=10)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", ondelete="cascade")
    hide = fields.Boolean(string="Hide")

    @api.model
    def split_multi_codes(self, limit=5000):
        """Split records holding several codes on one line into one record per code.

        Called daily by the "Alternative: Split multi-code records" cron, in batches.
        The first code stays on the original record; the others become new records
        with the same product, sequence and hide flag. Codes the product already has
        are not created again.
        """
        domain = [
            ("name", "!=", False),
            "|",
            ("name", "like", ";"),
            ("name", "like", ","),
        ]
        records = self.search(domain, limit=limit)
        if not records:
            return True

        # Codes already present on the products involved, to avoid duplicates.
        existing = {}
        tmpl_ids = records.product_tmpl_id.ids
        if tmpl_ids:
            for data in self.search_read([("product_tmpl_id", "in", tmpl_ids)], ["name", "product_tmpl_id"]):
                tmpl_id = data["product_tmpl_id"] and data["product_tmpl_id"][0]
                existing.setdefault(tmpl_id, set()).add((data["name"] or "").strip())

        vals_list = []
        split_count = 0
        skipped = 0
        for record in records:
            name = (record.name or "").strip()
            codes = [c.strip() for c in _CODE_SEPARATOR_RE.split(name) if c.strip()]
            if not codes:
                continue
            if len(codes) == 1:
                # A single code with a stray delimiter around it ("12345, ").
                if codes[0] != record.name:
                    record.write({"name": codes[0]})
                continue

            tmpl_id = record.product_tmpl_id.id or False
            product_codes = existing.setdefault(tmpl_id, set())
            record.write({"name": codes[0]})
            product_codes.add(codes[0])
            for code in codes[1:]:
                if code in product_codes:
                    skipped += 1
                    continue
                product_codes.add(code)
                vals_list.append(
                    {
                        "name": code,
                        "product_tmpl_id": tmpl_id,
                        "sequence": record.sequence,
                        "hide": record.hide,
                    }
                )
            split_count += 1

        if vals_list:
            self.create(vals_list)
        _logger.info(
            "Split alternative codes: %s records split, %s new codes, %s duplicates skipped",
            split_count,
            len(vals_list),
            skipped,
        )
        return True
