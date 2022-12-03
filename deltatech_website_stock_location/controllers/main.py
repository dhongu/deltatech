# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers import main as website_sale_controller


class WebsiteSale(website_sale_controller.WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):

        current_website = request.env["website"].get_current_website()
        request.context = dict(
            request.context, warehouse=current_website.warehouse_id, location=current_website.location_id.id
        )

        if not current_website.warehouse_id:
            request.context = dict(request.context, all_warehouses=True)
        if not current_website.location_id:
            request.context = dict(request.context, all_locations=True)

        response = super(WebsiteSale, self).shop(page, category, search, ppg, **post)

        return response


class PaymentPortal(website_sale_controller.PaymentPortal):
    @http.route()
    def shop_payment_transaction(self, *args, **kwargs):
        current_website = request.env["website"].get_current_website()
        request.context = dict(
            request.context, warehouse=current_website.warehouse_id, location=current_website.location_id.id
        )
        if not current_website.warehouse_id:
            request.context = dict(request.context, all_warehouses=True)
        if not current_website.location_id:
            request.context = dict(request.context, all_locations=True)
        return super().shop_payment_transaction(*args, **kwargs)
