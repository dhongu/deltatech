from odoo import models
from odoo.exceptions import AccessError

from .product import PRODUCT_MODELS, SECURITY_GROUP


class MailMessage(models.Model):
    _inherit = "mail.message"

    def unlink(self):
        # Direct deletions (ORM, RPC, scripts, other modules) must obey the same rule as the
        # chatter "Delete" action. The framework deletes messages in sudo (e.g. when a product
        # is deleted), so sudo is not blocked.
        if (
            not self.env.su
            and not self.env.user.has_group(SECURITY_GROUP)
            and any(message.model in PRODUCT_MODELS for message in self.sudo())
        ):
            raise AccessError(
                self.env._(
                    "You are not allowed to delete or edit chatter messages on products.\n"
                    "Ask an administrator to grant you the 'Delete Product Chatter Messages' group."
                )
            )
        return super().unlink()
