from odoo.tests.common import TransactionCase


class TestPartnerPhone(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a partner with phone and mobile
        self.partner_with_phone = self.env["res.partner"].create(
            {
                "name": "Partner with Phone",
                "phone": "123-456-7890",
            }
        )

        self.partner_with_mobile = self.env["res.partner"].create(
            {
                "name": "Partner with Mobile",
                "mobile": "098-765-4321",
            }
        )

        self.partner_with_no_contact = self.env["res.partner"].create(
            {
                "name": "Partner with No Contact",
            }
        )

        # Create account move records
        self.account_move_with_phone = self.env["account.move"].create(
            {
                "partner_id": self.partner_with_phone.id,
                "move_type": "out_invoice",  # Example move type
            }
        )

        self.account_move_with_mobile = self.env["account.move"].create(
            {
                "partner_id": self.partner_with_mobile.id,
                "move_type": "out_invoice",
            }
        )

        self.account_move_with_no_contact = self.env["account.move"].create(
            {
                "partner_id": self.partner_with_no_contact.id,
                "move_type": "out_invoice",
            }
        )

        # Create sale order records
        self.sale_order_with_phone = self.env["sale.order"].create(
            {
                "partner_id": self.partner_with_phone.id,
            }
        )

        self.sale_order_with_mobile = self.env["sale.order"].create(
            {
                "partner_id": self.partner_with_mobile.id,
            }
        )

        self.sale_order_with_no_contact = self.env["sale.order"].create(
            {
                "partner_id": self.partner_with_no_contact.id,
            }
        )

    def test_account_move_phone_computation(self):
        # Compute the phone field
        self.account_move_with_phone._compute_phone()
        self.assertEqual(
            self.account_move_with_phone.partner_phone,
            "123-456-7890",
            "The phone should be set from the partner's phone.",
        )

        self.account_move_with_mobile._compute_phone()
        self.assertEqual(
            self.account_move_with_mobile.partner_phone,
            "098-765-4321",
            "The phone should be set from the partner's mobile.",
        )

        self.account_move_with_no_contact._compute_phone()
        self.assertFalse(
            self.account_move_with_no_contact.partner_phone,
            "The phone should be False for a partner with no contact details.",
        )

    def test_sale_order_phone_computation(self):
        # Compute the phone field
        self.sale_order_with_phone._compute_phone()
        self.assertEqual(
            self.sale_order_with_phone.partner_phone,
            "123-456-7890",
            "The phone should be set from the partner's phone.",
        )

        self.sale_order_with_mobile._compute_phone()
        self.assertEqual(
            self.sale_order_with_mobile.partner_phone,
            "098-765-4321",
            "The phone should be set from the partner's mobile.",
        )

        self.sale_order_with_no_contact._compute_phone()
        self.assertFalse(
            self.sale_order_with_no_contact.partner_phone,
            "The phone should be False for a partner with no contact details.",
        )
