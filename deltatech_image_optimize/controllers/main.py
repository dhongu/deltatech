# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from ..models.ir_attachment import BG_METHODS, _rembg_available

# modelele ale căror imagini apar în editorul de website cu butonul „Remove background”
EDITOR_MODELS = ("product.template", "product.product", "product.image")


class ImageBackgroundController(http.Controller):
    def _dt_bg_record(self, model, res_id):
        """Recordul a cărui imagine o arată editorul, verificat pentru scriere.

        Varianta fără imagine proprie arată imaginea șablonului: decupajul se
        face atunci pe șablon, ca și în pagină.
        """
        if model not in EDITOR_MODELS:
            raise AccessError(request.env._("The background can only be removed from product pictures."))
        record = request.env[model].browse(int(res_id)).exists()
        if not record:
            raise UserError(request.env._("The product of this picture no longer exists."))
        if model == "product.product" and not record.image_variant_1920:
            record = record.product_tmpl_id
        record.check_access("write")
        if not record[record._dt_bg_image_field]:
            raise UserError(request.env._("This product has no picture."))
        return record

    def _dt_bg_params(self, method):
        params = request.env["ir.attachment"]._dt_bg_params()
        if method in BG_METHODS:
            params["method"] = method
        return params

    @http.route("/deltatech_image_optimize/bg/preview", type="jsonrpc", auth="user")
    def bg_preview(self, model, res_id, method=None):
        """Imaginea înainte și după eliminarea fundalului, fără să scrie nimic."""
        record = self._dt_bg_record(model, res_id)
        params = self._dt_bg_params(method)
        data, warning = record._dt_bg_cutout(params)
        before = record[record._dt_bg_variant_fields[0]] or record[record._dt_bg_image_field]
        return {
            "method": params["method"],
            "rembg": _rembg_available(),
            "before": before.to_base64(),
            "after": data and base64.b64encode(data).decode(),
            "warning": warning or False,
        }

    @http.route("/deltatech_image_optimize/bg/apply", type="jsonrpc", auth="user")
    def bg_apply(self, model, res_id, method=None):
        """Elimină fundalul și scrie imaginea, cu aceeași metodă ca în previzualizare."""
        record = self._dt_bg_record(model, res_id)
        data, warning = record._dt_bg_cutout(self._dt_bg_params(method))
        if not data:
            raise UserError(warning or request.env._("The background could not be removed."))
        record._dt_bg_apply(data)
        return True
