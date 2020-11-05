# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAlternativeLink(WebsiteSale):
    @http.route(["/shop/product-code/<code>"], type="http", auth="public", website=True, sitemap=False)
    def product_by_code(self, code="", **kwargs):
        product = request.env["product.template"].search([("default_code", "=", code)], limit=1)
        if not product:
            raise request.not_found()
        return self.product(product, **kwargs)

    @http.route(["/shop/products-json"], type="json", auth="public", website=True, sitemap=False)
    def products_json_by_code(self, search="", **kwargs):
        res = self._search_products_by_code()
        return res

    @http.route(["/shop/products-search"], type="http", auth="public", website=True, sitemap=False)
    def products_search_by_code(self, search="", **kwargs):
        res = self._search_products_by_code()
        return str(res)

    def _search_products_by_code(self):
        domain = request.website.sale_product_domain()
        products = request.env["product.template"].sudo().search(domain, limit=100)
        res = []
        alternative_code_mod = request.env["ir.module.module"].search(
            [("name", "=", "deltatech_alternative"), ("state", "=", "installed")]
        )

        for product in products:
            combination_info = product._get_combination_info()
            values = {
                "name": combination_info["display_name"],
                "default_code": product.default_code,
                "price": combination_info["price"],
                "list_price": combination_info["list_price"],
                "image": product.image,
            }
            if alternative_code_mod:
                alternative_code = []
                for alternative in product.alternative_ids:
                    alternative_code += [{"name": alternative.name, "hide": alternative.hide}]
                values["alternative_code"] = alternative_code

            res += [values]

        return res
