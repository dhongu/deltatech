# ©  2023 Deltatech
# See README.rst file on addons root folder for license details
"""Settings for the process library source discovery."""

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    process_library_autodiscover = fields.Boolean(
        string="Discover processes from all modules",
        config_parameter="deltatech_business_process.process_library_autodiscover",
        default=True,
        help="Scan every installed module that ships a `processes/` folder. Disabled = only the modules listed below.",
    )
    process_library_whitelist = fields.Char(
        string="Restrict to modules (list)",
        config_parameter="deltatech_business_process.process_library_whitelist",
        help="Comma-separated list of modules. When set, the sources are "
        "restricted to exactly the listed modules (ignores auto-discovery).",
    )
