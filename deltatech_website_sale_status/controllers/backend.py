# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http

from odoo.addons.website_sale.controllers.backend import WebsiteSaleBackend

# from odoo.http import request


class WebsiteSaleBackendInherit(WebsiteSaleBackend):
    @http.route()
    def fetch_dashboard_data(self, website_id, date_from, date_to):
        # Website = request.env["website"]
        # current_website = website_id and Website.browse(website_id) or Website.get_current_website()

        results = super(WebsiteSaleBackendInherit, self).fetch_dashboard_data(website_id, date_from, date_to)

        return results
