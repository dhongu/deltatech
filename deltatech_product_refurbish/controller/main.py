from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleProductRefurbish(WebsiteSale):
    @http.route(["/shop/cart/update"], type="http", auth="public", methods=["GET", "POST"], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        if not kw.get("lot_id"):
            return super(WebsiteSaleProductRefurbish, self).cart_update(product_id, add_qty, set_qty, **kw)

        # This route is called when adding a product to cart (no options).
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != "draft":
            request.session["sale_order_id"] = None
            sale_order = request.website.sale_get_order(force_create=True)

        sale_order._cart_refurbish_update(lot_id=int(kw.get("lot_id")), add_qty=add_qty, set_qty=set_qty)

        if kw.get("express"):
            return request.redirect("/shop/checkout?express=1")

        return request.redirect("/shop/cart")
