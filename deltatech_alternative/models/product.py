# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.osv import expression
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
        for product in self:
            product.search_index = " ".join([product.name, product.default_code or ""])
            if product.seller_ids:
                product.search_index += " ".join([s.product_code or "" for s in product.seller_ids])
            if product.alternative_ids:
                product.search_index += " ".join([a.name or "" for a in product.alternative_ids])
            product.search_index = product.search_index[:1000]

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
        if name and safe_eval(get_param("deltatech_alternative_website.search_index", False)):
            domain = [("search_index", operator, name)]
            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        else:
            return super(ProductProduct, self)._name_search(
                name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
            )


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if name and safe_eval(get_param("deltatech_alternative_website.search_index", False)):
            domain = [("search_index", operator, name)]
            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        else:
            return super(ProductProduct, self)._name_search(
                name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
            )


class ProductAlternative(models.Model):
    _name = "product.alternative"
    _description = "Product alternative"

    name = fields.Char(string="Code", index=True)
    sequence = fields.Integer(string="sequence", default=10)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", ondelete="cascade")
    hide = fields.Boolean(string="Hide")
