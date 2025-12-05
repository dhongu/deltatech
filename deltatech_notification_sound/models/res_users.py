# © 2025 Terrabit, Dorin Hongu
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    notification_sound_enabled = fields.Boolean(
        string="Enable notification sounds",
        default=True,
        help="If enabled, the backend will play a short sound when a notification is shown.",
    )
