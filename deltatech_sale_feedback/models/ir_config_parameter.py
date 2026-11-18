# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    def get_param(self, key, default=False):
        # the base url of the company website is passed in the context by
        # request_feedback; it must not go through the cached _get_param, whose
        # cache key ignores the context and would hand the value (or a missing
        # one) to every later call of the same process
        if key == "web.base.url" and self.env.context.get("web_base_url"):
            return self.env.context["web_base_url"]
        return super().get_param(key, default=default)
