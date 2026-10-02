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
