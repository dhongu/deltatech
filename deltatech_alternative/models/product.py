# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):
    _inherit = "product.template"

    search_index = fields.Char(compute="_compute_search_index", store=True, index=True, compute_sudo=True)

    alternative_code = fields.Char(
        string="Alternative Code", index=True, inverse="_inverse_alternative_code", compute="_compute_alternative_code"
    )
    alternative_ids = fields.One2many("product.alternative", "product_tmpl_id", string="Alternatives")

    used_for = fields.Char(string="Used For")

    @api.depends("name", "default_code", "alternative_ids.name", "seller_ids.product_code")
    def _compute_search_index(self):
        langs = self.env["res.lang"].search([("active", "=", True)])
        langs = langs.mapped("code")
        for product in self:
            names = [product.with_context(lang=lang).name for lang in langs]
            name_terms = list(set(names))
            good_terms = [term for term in name_terms if term is not False]
            search_index = " ".join(good_terms)

            if product.default_code:
                search_index = product.default_code + " " + search_index

            terms = []
            if product.seller_ids:
                terms += [s.product_code for s in product.seller_ids if s.product_code]
            if product.alternative_ids:
                terms += [a.name for a in product.alternative_ids if a.name]

            terms = list(set(terms))
            search_index += " " + " ".join(terms)
            product.search_index = search_index.upper()

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
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if name and safe_eval(get_param("deltatech_alternative_website.search_index", "False")):
            domain = [("search_index", operator, name)]

            if len(name) <= safe_eval(get_param("alternative.length_min", "3")):
                return 0

            if operator == "ilike":
                # cauta direct in SQL
                sql = """
                    SELECT product_product.id
                    FROM product_product
                    WHERE search_index ILIKE %s
                    LIMIT %s
                """
                self.env.cr.execute(sql, (f"%{name}%", limit))
                res = self.env.cr.fetchall()
                return [r[0] for r in res]

            return self.sudo()._search(domain, limit=limit, access_rights_uid=name_get_uid)
        else:
            return super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    @api.model
    def search_count(self, args):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if safe_eval(get_param("deltatech_alternative_website.search_index", "False")):
            # exista search_index in args
            for arg in args:
                if arg[0] == "search_index":
                    sql = """
                        SELECT COUNT(*)
                        FROM product_template
                        WHERE search_index ILIKE %s
                    """
                    self.env.cr.execute(sql, (f"%{arg[2]}%",))
                    res = self.env.cr.fetchone()
                    return res[0]
        return super().search_count(args)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if name and safe_eval(get_param("deltatech_alternative_website.search_index", "False")):
            domain = [("search_index", operator, name)]
            if len(name) <= safe_eval(get_param("alternative.length_min", "3")):
                return 0

            if operator == "ilike":
                # cauta direct in SQL
                sql = """
                    SELECT product_product.id
                    FROM product_product
                    JOIN product_template ON product_template.id = product_product.product_tmpl_id
                    WHERE search_index ILIKE %s
                    LIMIT %s
                """
                self.env.cr.execute(sql, (f"%{name}%", limit))
                res = self.env.cr.fetchall()
                return [r[0] for r in res]

            return self.sudo()._search(domain, limit=limit, access_rights_uid=name_get_uid)
        else:
            return super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    @api.model
    def search_count(self, args):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if safe_eval(get_param("deltatech_alternative_website.search_index", "False")):
            # exista search_index in args
            for arg in args:
                if arg[0] == "search_index" and len(arg) > safe_eval(get_param("alternative.length_min", "3")):
                    sql = """
                        SELECT COUNT(*)
                        FROM product_template
                        WHERE search_index ILIKE %s
                    """
                    self.env.cr.execute(sql, (f"%{arg[2]}%",))
                    res = self.env.cr.fetchone()
                    return res[0]
        return super().search_count(args)


class ProductAlternative(models.Model):
    _name = "product.alternative"
    _description = "Product alternative"

    name = fields.Char(string="Code", index=True)
    sequence = fields.Integer(string="sequence", default=10)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", ondelete="cascade")
    hide = fields.Boolean(string="Hide")
