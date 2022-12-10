# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.website_sale.controllers import main

#  FH312316, dc35407, CC106785


class Website(main.Website):
    @http.route()
    def autocomplete(self, search_type=None, term=None, order=None, limit=5, max_nb_chars=999, options=None):
        options = options or {}
        options["allowFuzzy"] = False
        return super().autocomplete(search_type, term, order, limit, max_nb_chars, options)


class WebsiteSale(main.WebsiteSale):
    def _get_search_options(
        self, category=None, attrib_values=None, pricelist=None, min_price=0.0, max_price=0.0, conversion_rate=1, **post
    ):
        options = super(WebsiteSale, self)._get_search_options(
            category, attrib_values, pricelist, min_price, max_price, conversion_rate, **post
        )
        options["allowFuzzy"] = False
        return options

    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        domains = super(WebsiteSale, self)._get_search_domain(search, category, attrib_values, search_in_description)
        if search:
            alternative_ids = request.env["product.alternative"]
            for srch in search.split(" "):
                alt_domain = [("name", "ilike", srch)]
                alternative_ids |= request.env["product.alternative"].search(alt_domain, limit=10)
            product_tmpl_ids = alternative_ids.mapped("product_tmpl_id")

            if product_tmpl_ids:
                subdomains = [("id", "in", list(product_tmpl_ids.ids))]
                domains = expression.OR([subdomains, domains])

        return domains
