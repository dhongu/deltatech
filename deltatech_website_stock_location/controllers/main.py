# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale as WebsiteSaleBase


class WebsiteSale(WebsiteSaleBase):
    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):

        current_website = request.env["website"].get_current_website()
        request.context = dict(request.context, location=current_website.location_id.id)
        response = super(WebsiteSale, self).shop(page, category, search, ppg, **post)

        return response
