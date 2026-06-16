# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    deltatech_browser_print_enabled = fields.Boolean(
        string="Use Zebra Browser Print",
        config_parameter="deltatech_report_prn.browser_print_enabled",
        help="Send ZPL/PRN labels directly to the printer through Zebra Browser "
        "Print installed on the workstation. When disabled (default), labels are "
        "downloaded as a .prn file and handled by the legacy workstation flow "
        "(file association + .bat). Even when enabled, the legacy flow is used "
        "automatically as a fallback on any workstation where Browser Print is "
        "not reachable.",
    )
