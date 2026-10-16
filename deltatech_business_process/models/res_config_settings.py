# ©  2023 Deltatech
# See README.rst file on addons root folder for license details
"""Settings for the process library source discovery."""

from odoo import api, fields, models
from odoo.tools import str2bool

AUTODISCOVER_PARAM = "deltatech_business_process.process_library_autodiscover"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Stored by hand as "1"/"0": with ``config_parameter`` a disabled Boolean deletes the
    # parameter, which then reads back as the enabled default.
    process_library_autodiscover = fields.Boolean(
        string="Discover processes from all modules",
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
    process_library_git_user = fields.Char(
        string="Git username",
        config_parameter="deltatech_business_process.process_library_git_user",
        help="Username for private HTTPS repositories. Leave empty to use "
        "'x-access-token' (works for GitHub personal access tokens). "
        "For GitLab use 'oauth2'.",
    )
    process_library_git_token = fields.Char(
        string="Git token / password",
        config_parameter="deltatech_business_process.process_library_git_token",
        help="Personal access token (or password) for private HTTPS repositories. "
        "It is sent as an HTTP Basic Authorization header on each git command and "
        "is never written into the cloned repo's on-disk config. SSH (git@…) URLs "
        "and URLs that already embed credentials ignore this and use their own auth.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        value = self.env["ir.config_parameter"].sudo().get_param(AUTODISCOVER_PARAM, "1")
        res["process_library_autodiscover"] = str2bool(value, True)
        return res

    def set_values(self):
        res = super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            AUTODISCOVER_PARAM, "1" if self.process_library_autodiscover else "0"
        )
        return res

    def action_sync_git_repos(self):
        synced = self.env["business.process.library"].sync_git_repos()
        if synced:
            names = ", ".join(label for label, _ in synced)
            msg = self.env._("Synced: %s") % names
        else:
            msg = self.env._("No git repositories configured or sync failed.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": self.env._("Process Library — Git Sync"), "message": msg, "sticky": False},
        }
