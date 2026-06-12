# ©  2023 Deltatech
# See README.rst file on addons root folder for license details
"""Settings for the process library source discovery."""

from odoo import _, fields, models


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
    process_library_git_repos = fields.Char(
        string="Git repositories",
        config_parameter="deltatech_business_process.process_library_git_repos",
        help="Comma-separated list of git URLs. Each repo is cloned/pulled "
        "into the Odoo data directory and scanned for process.json files. "
        "Example: https://github.com/terrabit-ro/procese",
    )

    def action_sync_git_repos(self):
        synced = self.env["business.process.library"].sync_git_repos()
        if synced:
            names = ", ".join(label for label, _ in synced)
            msg = _("Synced: %s") % names
        else:
            msg = _("No git repositories configured or sync failed.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": _("Process Library — Git Sync"), "message": msg, "sticky": False},
        }
