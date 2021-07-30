# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteSaleAlternativeLink(WebsiteSale):
    @http.route(["/shop/product-code/<code>"], type="http", auth="public", website=True, sitemap=False)
    def product_by_code(self, code="", **kwargs):
        product = request.env["product.template"].search([("default_code", "=", code)], limit=1)
        if not product:
            raise request.not_found()
        return self.product(product, **kwargs)

    @http.route(["/shop/products-json"], type="json", auth="public", website=True, sitemap=False)
    def products_json_by_code(self, search="", **kwargs):
        res = self._search_products_by_code(search)
        return res

    @http.route(["/shop/products-search"], type="http", auth="public", website=True, sitemap=False)
    def products_search_by_code(self, search="", **kwargs):
        res = self._search_products_by_code(search)
        return str(res)

    def _search_products_by_code(self, search):

        domain = request.website.sale_product_domain()
        _logger.info("_search_products_by_code: %s", search)
        if search:
            for srch in search.split(" "):
                domain += [
                    "|",
                    "|",
                    "|",
                    ("name", "ilike", srch),
                    ("description", "ilike", srch),
                    ("description_sale", "ilike", srch),
                    ("product_variant_ids.default_code", "ilike", srch),
                ]

        products = request.env["product.template"].with_context(bin_size=True).sudo().search(domain, limit=10)
        res = []
        alternative_code_mod = (
            request.env["ir.module.module"]
            .sudo()
            .search([("name", "=", "deltatech_alternative"), ("state", "=", "installed")])
        )
        pricelist = request.website.get_current_pricelist()
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for product in products:
            if product.is_published:
                combination_info = product._get_combination_info(pricelist=pricelist)
                values = {
                    "name": combination_info["display_name"],
                    "default_code": product.default_code,
                    "categories": [],
                    "price": combination_info["price"],
                    "list_price": combination_info["list_price"],
                    "image_url": base_url + "/web/image/product.template/" + str(product.id) + "/image/",
                }
                for categ in product.public_categ_ids:
                    values["categories"] += [categ.display_name]
                if alternative_code_mod:
                    alternative_code = []
                    for alternative in product.alternative_ids:
                        alternative_code += [{"name": alternative.name, "hide": alternative.hide}]
                    values["alternative_code"] = alternative_code

                res += [values]

        return res
