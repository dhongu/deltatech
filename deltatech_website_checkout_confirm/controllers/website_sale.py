from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, tools, _
from odoo.http import request

class WebsiteSaleCheckout(WebsiteSale):

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def payment_confirmation(self, **post):
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            order.action_confirm()
        return super(WebsiteSaleCheckout, self).payment_confirmation(**post)

