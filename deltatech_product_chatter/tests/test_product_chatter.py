from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductChatter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = cls.env.ref("deltatech_product_chatter.group_delete_product_chatter")
        groups = cls.env.ref("base.group_user") | cls.env.ref("product.group_product_manager")
        cls.user = cls.env["res.users"].create(
            {"name": "Product Editor", "login": "product_editor", "group_ids": [(6, 0, groups.ids)]}
        )
        cls.template = cls.env["product.template"].create({"name": "Chatter Product"})
        cls.variant = cls.template.product_variant_id

    def _post(self, record):
        return record.with_user(self.user).message_post(body="Hello", message_type="comment")

    def test_unlink_blocked_without_group(self):
        for record in (self.template, self.variant):
            message = self._post(record)
            with self.assertRaises(AccessError):
                message.with_user(self.user).unlink()
            self.assertTrue(message.exists())

    def test_unlink_allowed_with_group(self):
        self.user.group_ids = [(4, self.group.id)]
        for record in (self.template, self.variant):
            message = self._post(record)
            message.with_user(self.user).unlink()
            self.assertFalse(message.exists())

    def test_unlink_other_models_not_restricted(self):
        self.user.group_ids = [(4, self.env.ref("base.group_partner_manager").id)]
        # with account installed, deleting any message runs the accounting audit-log check,
        # which searches journal entries and needs read access on them
        account_readonly = self.env.ref("account.group_account_readonly", raise_if_not_found=False)
        if account_readonly:
            self.user.group_ids = [(4, account_readonly.id)]
        partner = self.env["res.partner"].create({"name": "Chatter Partner"})
        message = partner.with_user(self.user).message_post(body="Hello", message_type="comment")
        message.with_user(self.user).unlink()
        self.assertFalse(message.exists())

    def test_sudo_and_product_deletion_not_blocked(self):
        message = self._post(self.template)
        message.sudo().unlink()
        self.assertFalse(message.exists())

        template = self.env["product.template"].create({"name": "Chatter To Delete"})
        message = self._post(template)
        template.with_user(self.user).unlink()
        self.assertFalse(message.exists())

    def test_edit_blocked_without_group(self):
        message = self._post(self.template)
        with self.assertRaises(AccessError):
            self.template.with_user(self.user)._check_can_update_message_content(message.sudo())
        self.user.group_ids = [(4, self.group.id)]
        self.template.with_user(self.user)._check_can_update_message_content(message.sudo())
