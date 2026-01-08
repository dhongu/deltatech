# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http

from odoo.addons.website_sale.controllers import main, website


class Website(website.Website):
    @http.route()
    def autocomplete(
        self,
        search_type=None,
        term=None,
        order=None,
        limit=5,
        max_nb_chars=999,
        options=None,
    ):
        options = options or {}
        options["allowFuzzy"] = False
        return super().autocomplete(search_type, term, order, limit, max_nb_chars, options)


class WebsiteSale(main.WebsiteSale):
    def _get_search_options(
        self,
        category=None,
        attrib_values=None,
        tags=None,
        min_price=0.0,
        max_price=0.0,
        conversion_rate=1,
        **post,
    ):
        options = super()._get_search_options(
            category, attrib_values, tags, min_price, max_price, conversion_rate, **post
        )
        options["allowFuzzy"] = False
        return options
