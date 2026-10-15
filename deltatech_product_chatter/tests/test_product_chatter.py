from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestProductChatter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_basic = new_test_user(
            cls.env, login="chatter_basic", groups="base.group_user,base.group_partner_manager"
        )
        cls.user_allowed = new_test_user(
            cls.env,
            login="chatter_allowed",
            groups="base.group_user,base.group_partner_manager,deltatech_product_chatter.group_delete_product_chatter",
        )
        cls.template = cls.env["product.template"].create({"name": "Chatter Product"})
        cls.variant = cls.template.product_variant_id
        cls.partner = cls.env["res.partner"].create({"name": "Chatter Partner"})

    def _post(self, record):
        return record.message_post(body="Hello", message_type="comment")

    def test_template_blocked_without_group(self):
        message = self._post(self.template)
        with self.assertRaises(AccessError):
            self.template.with_user(self.user_basic)._message_update_content(message, body="")

    def test_variant_blocked_without_group(self):
        message = self._post(self.variant)
        with self.assertRaises(AccessError):
            self.variant.with_user(self.user_basic)._message_update_content(message, body="")

    def test_template_allowed_with_group(self):
        message = self._post(self.template)
        self.template.with_user(self.user_allowed)._message_update_content(message, body="Edited")
        self.assertIn("Edited", str(message.body))

    def test_other_models_unaffected(self):
        message = self._post(self.partner)
        self.partner.with_user(self.user_basic)._message_update_content(message, body="Edited")
        self.assertIn("Edited", str(message.body))

    def test_group_assigned_to_admin(self):
        group = self.env.ref("deltatech_product_chatter.group_delete_product_chatter")
        self.assertIn(self.env.ref("base.user_admin"), group.user_ids)
        self.assertEqual(group.privilege_id, self.env.ref("product.res_groups_privilege_product"))


@tagged("post_install", "-at_install")
class TestProductChatterUnlink(TransactionCase):
    """Direct deletion of product chatter messages (ORM/RPC) obeys the same rule as the UI"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = cls.env.ref("deltatech_product_chatter.group_delete_product_chatter")
        cls.user = new_test_user(
            cls.env, login="product_editor", groups="base.group_user,product.group_product_manager"
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
