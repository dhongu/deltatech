# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.tools import str2bool


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    # Default location of the (proprietary, not bundled) Browser Print SDK. A
    # private companion module that ships the SDK overrides this via the
    # `deltatech_report_prn.browser_print_sdk_url` system parameter, pointing to
    # its own static path. See readme/ROADMAP.md and static/lib/zebra/README.md.
    _BROWSER_PRINT_SDK_DEFAULT_URL = "/deltatech_report_prn/static/lib/zebra/BrowserPrint.min.js"

    def session_info(self):
        # Expose the Browser Print master switch and SDK url to the web client
        # so the PRN report handler can decide between Browser Print and the
        # legacy .prn download without an extra RPC. ir.config_parameter is not
        # readable by regular users over RPC, hence the sudo() here.
        result = super().session_info()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        result["deltatech_browser_print_enabled"] = str2bool(
            get_param("deltatech_report_prn.browser_print_enabled") or "False", default=False
        )
        result["deltatech_browser_print_sdk_url"] = (
            get_param("deltatech_report_prn.browser_print_sdk_url") or self._BROWSER_PRINT_SDK_DEFAULT_URL
        )
        return result
