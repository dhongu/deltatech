# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alternative_code = fields.Char(
        string="Alternative Code",
        index=True,
        inverse="_inverse_alternative_code",
        compute="_compute_alternative_code",
        unaccent=False,
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

    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
    #     product_ids = super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
    #     get_param = self.env["ir.config_parameter"].sudo().get_param
    #     if name and safe_eval(get_param("alternative.search_name", "False")):
    #         domain = [("name", operator, name)]
    #         alternatives = self.env["product.alternative"]._name_search(name, args=domain, operator=operator, limit=limit)
    #         if alternatives:
    #             product_ids |= alternatives.mapped("product_tmpl_id")
    #
    #     return product_ids


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        res = super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
        get_param = self.env["ir.config_parameter"].sudo().get_param
        res_ids = list(res)
        if name and safe_eval(get_param("alternative.search_name", "False")):
            domain = [("name", operator, name)]
            alternatives = self.env["product.alternative"].search(domain, limit=limit)
            if alternatives:
                product_tmpl_ids = alternatives.mapped("product_tmpl_id")
                product_ids = self._search(
                    [("product_tmpl_id", "in", product_tmpl_ids.ids)],
                    limit=limit,
                    access_rights_uid=name_get_uid,
                )
                res_ids.extend(list(product_ids))

        return res_ids


class ProductAlternative(models.Model):
    _name = "product.alternative"
    _description = "Product alternative"

    name = fields.Char(string="Code", index=True, unaccent=False)
    sequence = fields.Integer(string="sequence", default=10)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", ondelete="cascade")
    hide = fields.Boolean(string="Hide")
