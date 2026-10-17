from odoo import models
from odoo.exceptions import AccessError

from .product import PRODUCT_MODELS, SECURITY_GROUP

# Fields that hold the content of a message: changing them edits or "deletes" it.
CONTENT_FIELDS = {"body", "attachment_ids"}


class MailMessage(models.Model):
    _inherit = "mail.message"

    def _check_product_chatter_change(self):
        # Direct changes (ORM, RPC, scripts, other modules) must obey the same rule as the
        # chatter "Delete"/"Edit" actions. The framework works on messages in sudo (e.g. when
        # a product is deleted), so sudo is not blocked.
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

    def write(self, vals):
        if CONTENT_FIELDS.intersection(vals):
            self._check_product_chatter_change()
        return super().write(vals)

    def unlink(self):
        self._check_product_chatter_change()
        return super().unlink()
