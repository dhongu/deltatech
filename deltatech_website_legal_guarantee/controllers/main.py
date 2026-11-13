# © 2026 Deltatech
# See README.rst file on addons root folder for license details
from odoo import http
from odoo.http import request


class LegalGuarantee(http.Controller):
    @http.route(["/garantie"], type="http", auth="public", website=True, sitemap=True)
    def legal_guarantee(self, **kwargs):
        return request.render("deltatech_website_legal_guarantee.legal_guarantee_page")
