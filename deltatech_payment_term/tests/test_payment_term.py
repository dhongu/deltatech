from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPaymentTerm(TransactionCase):
    def test_payment_term_wizard(self):
        # Create a payment term
        payment_term = self.env["account.payment.term"].create(
            {
                "name": "Test Payment Term",
            }
        )

        # Create the wizard
        wizard = (
            self.env["account.payment.term.rate.wizard"]
            .with_context(active_model="account.payment.term", active_id=payment_term.id)
            .create(
                {"name": "Updated Payment Term", "rate": 3, "advance": 25.0, "day_of_the_month": 15, "value": "percent"}
            )
        )

        # Run the creation process
        wizard.do_create_rate()

        # Check if the payment term was updated
        self.assertEqual(payment_term.name, "Updated Payment Term")
        # We expect 4 lines (1 advance + 3 rates, but the last one is the balance)
        # Actually the code adds first_rate, then rate times norm_rate,
        # but then replaces the last one with a balance line.
        # So it's 1 (advance) + rate (norm_rates) = rate + 1 total lines.
        self.assertEqual(len(payment_term.line_ids), 4)
