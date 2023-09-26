# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, http
from odoo.http import request

from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):
    # todo: de generat o eroare mai ok - asa zice ca a expirat sesiunea
    # @http.route(auth="user")
    # def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
    #     return super(WebsiteSale, self).cart_update_json(product_id, line_id, add_qty, set_qty, display)
    #
    # @http.route(auth="user")
    # def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
    #     return super(WebsiteSale, self).cart_update(product_id, add_qty, set_qty, **kw)

    @http.route(["/shop/cart/update_json"], type="json", auth="public", methods=["POST"], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
        user = request.env.user
        if user._is_public():  # The user is not logged in
            response = {
                "cart_quantity": 0,
                "quantity": 0,
                "warning": _("Please login to add products to cart."),
            }
            return response
        return super().cart_update_json(
            product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, display=display, **kw
        )

    @http.route(auth="user")
    def checkout(self, **post):
        return super().checkout(**post)
