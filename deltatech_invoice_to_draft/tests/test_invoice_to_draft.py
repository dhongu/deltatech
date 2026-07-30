from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInvoiceToDraft(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_reset = cls.env.ref("deltatech_invoice_to_draft.group_reset_to_draft_account_move")
        cls.invoice = cls.init_invoice("in_invoice", products=cls.product_a + cls.product_b)
        cls.invoice.action_post()

    def _show_reset_to_draft_button(self):
        """Recompute the field, ignoring any value cached before the group changed."""
        self.invoice.invalidate_recordset(["show_reset_to_draft_button"])
        return self.invoice.show_reset_to_draft_button

    def test_reset_to_draft_hidden_without_group(self):
        """A user outside the group cannot reset a posted move to draft."""
        self.env.user.group_ids -= self.group_reset
        self.assertFalse(self.env.user.has_group("deltatech_invoice_to_draft.group_reset_to_draft_account_move"))
        self.assertFalse(
            self._show_reset_to_draft_button(),
            "Reset to Draft must stay hidden for a user without the dedicated group",
        )

    def test_reset_to_draft_visible_with_group(self):
        """A user in the group keeps the native Reset to Draft button.

        Together with the previous test this proves the group is what hides the button:
        the native compute allows it on this invoice, only the group gates it.
        """
        self.env.user.group_ids |= self.group_reset
        self.assertTrue(
            self._show_reset_to_draft_button(),
            "Reset to Draft must be available for a user in the dedicated group",
        )

    def test_button_draft_cancel(self):
        """The shortcut takes a posted move straight to cancelled."""
        self.assertEqual(self.invoice.state, "posted")
        self.invoice.button_draft_cancel()
        self.assertEqual(self.invoice.state, "cancel")
