# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


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
