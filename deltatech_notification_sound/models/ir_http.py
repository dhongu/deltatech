# © 2025 Terrabit, Dorin Hongu
from odoo import models


class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        info = super().session_info()
        user = self.env.user

        user_ctx = info.get("user_context", {})
        user_ctx["notification_sound_enabled"] = user.notification_sound_enabled
        info["user_context"] = user_ctx
        return info
