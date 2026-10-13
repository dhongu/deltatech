from odoo.exceptions import AccessError
from odoo.service.model import call_kw
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
        self.env.user.group_ids |= self.group_reset
        self.assertEqual(self.invoice.state, "posted")
        self.invoice.button_draft_cancel()
        self.assertEqual(self.invoice.state, "cancel")

    def _rpc(self, method):
        """Call a public method of the invoice the way the web client / XML-RPC does."""
        return call_kw(self.env["account.move"], method, [self.invoice.ids], {})

    def test_rpc_button_draft_without_group_refused(self):
        """DRAFTACCESS-001: a direct remote call of button_draft is refused without the group."""
        self.env.user.group_ids -= self.group_reset
        with self.assertRaises(AccessError):
            self._rpc("button_draft")
        self.assertEqual(self.invoice.state, "posted")

    def test_rpc_button_cancel_posted_without_group_refused(self):
        """button_cancel on a posted move resets it to draft first: refused without the group."""
        self.env.user.group_ids -= self.group_reset
        with self.assertRaises(AccessError):
            self._rpc("button_cancel")
        self.assertEqual(self.invoice.state, "posted")

    def test_button_draft_cancel_without_group_refused(self):
        """The Cancel Entry shortcut follows the same permission."""
        self.env.user.group_ids -= self.group_reset
        with self.assertRaises(AccessError):
            self._rpc("button_draft_cancel")
        with self.assertRaises(AccessError):
            self.invoice.button_draft_cancel()
        self.assertEqual(self.invoice.state, "posted")

    def test_rpc_button_draft_with_group_allowed(self):
        self.env.user.group_ids |= self.group_reset
        self._rpc("button_draft")
        self.assertEqual(self.invoice.state, "draft")

    def test_superuser_not_blocked(self):
        self.env.user.group_ids -= self.group_reset
        call_kw(self.env["account.move"].sudo(), "button_draft", [self.invoice.ids], {})
        self.assertEqual(self.invoice.state, "draft")

    def test_internal_flows_not_blocked(self):
        """Server code resetting a move as part of another flow is not blocked by the group."""
        self.env.user.group_ids -= self.group_reset
        # payment reset to draft resets its journal entry through button_draft
        payment = self.init_payment(100.0, post=True)
        self.assertTrue(payment.move_id)
        call_kw(self.env["account.payment"], "action_draft", [payment.ids], {})
        self.assertEqual(payment.move_id.state, "draft")
        # direct server-side call (not a remote request), e.g. from another module
        self.invoice.button_draft()
        self.assertEqual(self.invoice.state, "draft")
