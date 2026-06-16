# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.tools import str2bool


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        # Expose the Browser Print master switch to the web client so the PRN
        # report handler can decide between Browser Print and the legacy .prn
        # download without an extra RPC. ir.config_parameter is not readable by
        # regular users over RPC, hence the sudo() here.
        result = super().session_info()
        param = self.env["ir.config_parameter"].sudo().get_param("deltatech_report_prn.browser_print_enabled")
        result["deltatech_browser_print_enabled"] = str2bool(param or "False", default=False)
        return result
