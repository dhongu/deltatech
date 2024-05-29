# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleQty(WebsiteSale):

    # functa cart_update_json este mostenita in website_sale_loyalty
    @http.route()
    def cart_update_json(self, **kwargs):
        product_id = kwargs.get("product_id", None)
        if product_id:
            product = request.env["product.product"].sudo().browse(product_id)
        add_qty = kwargs.get("add_qty", None)
        set_qty = kwargs.get("set_qty", None)
        if product_id and (add_qty or set_qty):
            line = request.env["sale.order.line"].sudo()
            set_qty = line.fix_qty_multiple(product, product.uom_id, add_qty)
            kwargs["set_qty"] = set_qty
        value = super().cart_update_json(**kwargs)
        if product_id and (add_qty or set_qty):
            line = request.env["sale.order.line"].sudo()
            value["quantity"] = line.fix_qty_multiple(product, product.uom_id, value.get("quantity", 0))
        return value
