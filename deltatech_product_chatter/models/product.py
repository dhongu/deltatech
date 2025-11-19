from odoo import _, models
from odoo.exceptions import AccessError

PRODUCT_MODELS = {"product.template", "product.product"}
SECURITY_GROUP = "deltatech_product_chatter.group_delete_product_chatter"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _check_can_update_message_content(self, message):
        # Let standard rules run first (author/editor permissions, etc.)
        res = super()._check_can_update_message_content(message)
        # Then enforce our restriction specifically for product chatter
        # "Delete" in UI is implemented as editing the message to empty content
        # through /mail/message/update_content, so guard that path here.
        if message and message.model in PRODUCT_MODELS:
            if not self.env.user.has_group(SECURITY_GROUP):
                raise AccessError(
                    _(
                        "You are not allowed to delete or edit chatter messages on products.\n"
                        "Ask an administrator to grant you the 'Delete Product Chatter Messages' group."
                    )
                )
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _check_can_update_message_content(self, message):
        res = super()._check_can_update_message_content(message)
        if message and message.model in PRODUCT_MODELS:
            if not self.env.user.has_group(SECURITY_GROUP):
                raise AccessError(
                    _(
                        "You are not allowed to delete or edit chatter messages on products.\n"
                        "Ask an administrator to grant you the 'Delete Product Chatter Messages' group."
                    )
                )
        return res
