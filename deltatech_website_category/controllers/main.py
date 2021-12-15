# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http

from odoo.addons.website_sale.controllers.main import WebsiteSale as WebsiteSaleBase


class WebsiteSale(WebsiteSaleBase):
    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        if isinstance(category, str) and search:
            category = False
        return super(WebsiteSale, self).shop(page=page, category=category, search=search, ppg=ppg, **post)
