# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleQty(WebsiteSale):
    @http.route()
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        product = request.env["product.product"].sudo().browse(product_id)
        set_qty = request.env["sale.order.line"].sudo().fix_qty_multiple(product, product.uom_id, set_qty)

        value = super(WebsiteSaleQty, self).cart_update_json(product_id, line_id, add_qty, set_qty, display)
        product = request.env["product.product"].sudo().browse(product_id)
        value["quantity"] = (
            request.env["sale.order.line"].sudo().fix_qty_multiple(product, product.uom_id, value["quantity"])
        )
        return value
