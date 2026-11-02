# © 2026 Terrabit
# See README.rst file on addons root folder for license details

import re

from odoo import models
from odoo.http import request

# /<key>.txt: the key file that proves to IndexNow that the site is ours
KEY_FILE_RE = re.compile(r"^/([a-zA-Z0-9-]{8,128})\.txt$")


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _serve_fallback(cls):
        # a fallback, not a route: a route on /<key>.txt would hide the other .txt files of the site
        match = KEY_FILE_RE.match(request.httprequest.path)
        if match:
            website = request.env["website"].sudo().get_current_website()
            if website.indexnow_enabled and website.indexnow_key == match.group(1):
                return request.make_response(
                    website.indexnow_key, headers=[("Content-Type", "text/plain; charset=utf-8")]
                )
        return super()._serve_fallback()
