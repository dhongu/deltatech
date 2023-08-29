# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.tools import ormcache


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    @ormcache("self.env.uid", "self.env.su", "key")
    def _get_param(self, key):
        if key == "web.base.url" and self.env.context.get("web_base_url", False):
            return self.env.context.get("web.base.url")
        return super(IrConfigParameter, self)._get_param(key)
