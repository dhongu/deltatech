from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.us")

    def setUp(self):
        super().setUp()

        # Create an account.move record
        self.account_move = self.env["account.move"].create(
            {
                "name": "Test Move",
                "move_type": "entry",
            }
        )

    def test_show_reset_to_draft_button(self):
        # Check the _compute_show_reset_to_draft_button method
        self.account_move._compute_show_reset_to_draft_button()
        self.assertEqual(
            self.account_move.show_reset_to_draft_button,
            self.env.user.has_group("deltatech_invoice_to_draft.group_reset_to_draft_account_move"),
            "The show_reset_to_draft_button field should be computed correctly",
        )

    def test_button_draft_cancel(self):
        # Check the button_draft_cancel method
        self.account_move.button_draft_cancel()
        self.assertEqual(
            self.account_move.state,
            "cancel",
            "The state of the account move should be 'cancel' after calling button_draft_cancel",
        )
