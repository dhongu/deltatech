from odoo import models
from odoo.exceptions import AccessError

PRODUCT_MODELS = {"product.template", "product.product"}
SECURITY_GROUP = "deltatech_product_chatter.group_delete_product_chatter"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _check_product_chatter_access(self, messages):
        # "Delete" in UI is implemented as editing the message to empty content
        # through /mail/message/update_content, so guard that path here.
        if any(message.model in PRODUCT_MODELS for message in messages):
            if not self.env.user.has_group(SECURITY_GROUP):
                raise AccessError(
                    self.env._(
                        "You are not allowed to delete or edit chatter messages on products.\n"
                        "Ask an administrator to grant you the 'Delete Product Chatter Messages' group."
                    )
                )

    def _check_can_update_message_content(self, messages):
        # Let standard rules run first (author/editor permissions, etc.)
        res = super()._check_can_update_message_content(messages)
        # Then enforce our restriction specifically for product chatter
        self._check_product_chatter_access(messages)
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _check_product_chatter_access(self, messages):
        if any(message.model in PRODUCT_MODELS for message in messages):
            if not self.env.user.has_group(SECURITY_GROUP):
                raise AccessError(
                    self.env._(
                        "You are not allowed to delete or edit chatter messages on products.\n"
                        "Ask an administrator to grant you the 'Delete Product Chatter Messages' group."
                    )
                )

    def _check_can_update_message_content(self, messages):
        res = super()._check_can_update_message_content(messages)
        self._check_product_chatter_access(messages)
        return res
