# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.http import request


class ProductCatalog(models.Model):
    _inherit = "product.catalog"

    public_categ_ids = fields.Many2many(
        "product.public.category",
        string="Public Category",
        help="Those categories are used to group similar products for e-commerce.",
    )

    def create_product(self):
        products = super(ProductCatalog, self).create_product()
        for prod_cat in self:
            if prod_cat.public_categ_ids and prod_cat.product_id:
                prod_cat.product_id.public_categ_ids = prod_cat.public_categ_ids
        products.website_published = True
        return products


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        res = super(ProductTemplate, self)._search(
            args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid
        )
        # daca este o cautare de pe website
        if not res and not any(term[0] == "id" for term in (args or [])):
            args = list(args)
            for index in range(len(args)):
                if args[index][0] == "name":
                    code = args[index][2]

                    req_url = request.httprequest.url
                    if (
                        not res
                        and self.env.context.get("website_id")
                        and not limit  # in cautarea incrmentala se folosete limita de 5
                        and "/autocomplete" not in req_url
                    ):
                        prod_cat = self.env["product.catalog"].search([("code", "=ilike", code)], limit=1)

                        if prod_cat:
                            if not prod_cat.product_id:
                                prod_cat.create_product()

                            res = prod_cat.product_id.product_tmpl_id.id

        return res
