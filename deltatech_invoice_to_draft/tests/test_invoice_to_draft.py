from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveInInvoiceOnchanges(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.invoice = cls.init_invoice("in_invoice", products=cls.product_a + cls.product_b)
        cls.invoice.action_post()

    def test_show_reset_to_draft_button(cls):
        # Check the _compute_show_reset_to_draft_button method
        cls.invoice._compute_show_reset_to_draft_button()
        cls.assertEqual(
            cls.invoice.show_reset_to_draft_button,
            cls.env.user.has_group("deltatech_invoice_to_draft.group_reset_to_draft_account_move"),
            "The show_reset_to_draft_button field should be computed correctly",
        )

    def test_button_draft_cancel(cls):
        # Check the button_draft_cancel method
        cls.invoice.button_draft_cancel()
        cls.assertEqual(
            cls.invoice.state,
            "cancel",
            "The state of the account move should be 'cancel' after calling button_draft_cancel",
        )
