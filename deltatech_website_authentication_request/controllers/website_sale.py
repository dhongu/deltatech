# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http

from odoo.addons.website_sale.controllers.main import WebsiteSale as WebsiteSaleBase


class WebsiteSale(WebsiteSaleBase):
    @http.route(auth="user")
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        return super(WebsiteSale, self).cart_update_json(product_id, line_id, add_qty, set_qty, display)

    @http.route(auth="user")
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        return super(WebsiteSale, self).cart_update(product_id, add_qty, set_qty, **kw)

    @http.route(auth="user")
    def checkout(self, **post):
        return super(WebsiteSale, self).checkout(**post)
