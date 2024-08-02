# tests/test_partner_discount.py

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestPartnerDiscount(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a user without the discount group
        self.user_no_discount = self.env["res.users"].create(
            {
                "name": "User No Discount",
                "login": "user_no_discount",
                "groups_id": [(6, 0, [])],
            }
        )

        # Create a user with the discount group
        self.discount_group = self.env.ref("deltatech_partner_discount.group_partner_discount")
        self.user_with_discount = self.env["res.users"].create(
            {
                "name": "User With Discount",
                "login": "user_with_discount",
                "groups_id": [(6, 0, [self.discount_group.id])],
            }
        )

        # Create a partner
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "discount": 0.0,
            }
        )

        # Create an account move
        self.account_move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.general_journal = self.env["account.journal"].create(
            {
                "name": "General Journal",
                "code": "GEN",
                "type": "general",
            }
        )

    def test_check_discount_group_with_group(self):
        self.env = self.env(user=self.user_with_discount)
        self.partner.discount = 10.0
        self.assertEqual(self.partner.discount, 10.0)

    def test_create_partner_with_discount_no_group(self):
        self.env = self.env(user=self.user_no_discount)
        with self.assertRaises(UserError):
            self.env["res.partner"].create(
                {
                    "name": "New Partner",
                    "discount": 10.0,
                }
            )

    def test_account_move_partner_discount(self):
        self.assertEqual(self.account_move.partner_discount, self.partner.discount)
        self.partner.discount = 5.0
        self.assertEqual(self.account_move.partner_discount, self.partner.discount)
