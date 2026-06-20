from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    deltatech_tc_update_repo = fields.Char(
        string="TC Update Repository",
        config_parameter="deltatech_tc.update_repo",
        help="GitHub repo (owner/name) where Terrabit Connect agent releases are published.",
    )
    deltatech_tc_update_token = fields.Char(
        string="TC Update Token",
        config_parameter="deltatech_tc.update_token",
        help="Fine-grained read-only GitHub token (Contents) for the private agent repo. "
        "Stays server-side; stations never receive it — Odoo proxies the download.",
    )
