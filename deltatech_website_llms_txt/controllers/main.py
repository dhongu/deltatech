# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request


class WebsiteLlmsTxt(http.Controller):
    @http.route("/llms.txt", type="http", auth="public", website=True, multilang=False, sitemap=False)
    def llms_txt(self, **kwargs):
        website = request.website
        if not website.llms_txt_enabled:
            raise request.not_found()
        content = website.sudo()._get_llms_txt()
        return request.make_response(content, headers=[("Content-Type", "text/plain; charset=utf-8")])
