# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alternative_code = fields.Char(string="Alternative Code", index=True, compute="_compute_alternative_code")
    alternative_ids = fields.One2many("product.alternative", "product_tmpl_id", string="Alternatives")

    used_for = fields.Char(string="Used For")

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
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if "not" in operator:
            return super(ProductTemplate, self).name_search(name, args, operator=operator, limit=limit)

        args = args or []
        res_alt = []

        get_param = self.env["ir.config_parameter"].sudo().get_param
        alternative_search = safe_eval(get_param("alternative.search_name", "True"))
        catalog_search = safe_eval(get_param("alternative.search_catalog", "True"))

        if alternative_search and name and len(name) > 2:

            if alternative_search:
                alternative_ids = self.env["product.alternative"].search([("name", operator, name)], limit=10)
                products = alternative_ids.mapped("product_tmpl_id")
                if products:
                    res_alt = products.name_get()
                    args = expression.AND([args, [("id", "not in", products.ids)]])

        this = self.with_context({"no_catalog": True})
        res = super(ProductTemplate, this).name_search(name, args, operator=operator, limit=limit) + res_alt

        if not res and catalog_search:
            prod = self.env["product.catalog"].search_in_catalog(name)
            if prod:
                res = prod.product_tmpl_id.name_get()

        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if "not" in operator:
            return super(ProductProduct, self).name_search(name, args, operator=operator, limit=limit)

        args = args or []
        res_alt = []

        get_param = self.env["ir.config_parameter"].sudo().get_param
        alternative_search = safe_eval(get_param("alternative.search_name", "True"))
        catalog_search = safe_eval(get_param("alternative.search_catalog", "True"))

        if alternative_search and name and len(name) > 2:

            if alternative_search:
                alternative_ids = self.env["product.alternative"].search([("name", operator, name)], limit=10)
                products = alternative_ids.mapped("product_tmpl_id").mapped("product_variant_ids")
                if products:
                    res_alt = products.name_get()
                    args = expression.AND([args, [("id", "not in", products.ids)]])

        this = self.with_context({"no_catalog": True})
        res = super(ProductProduct, this).name_search(name, args, operator=operator, limit=limit) + res_alt

        if not res and catalog_search:
            prod = self.env["product.catalog"].search_in_catalog(name)
            if prod:
                res = prod.name_get()

        return res


class ProductAlternative(models.Model):
    _name = "product.alternative"
    _description = "Product alternative"

    name = fields.Char(string="Code", index=True)
    sequence = fields.Integer(string="sequence", default=10)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", ondelete="cascade")
    hide = fields.Boolean(string="Hide")
