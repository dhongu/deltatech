# tests/test_partner_discount.py

from odoo.exceptions import UserError
from odoo.service.model import call_kw
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPartnerDiscount(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a user without the discount group
        self.user_no_discount = self.env["res.users"].create(
            {
                "name": "User No Discount",
                "login": "user_no_discount",
                "group_ids": [(6, 0, [])],
            }
        )

        # Create a user with the discount group
        self.discount_group = self.env.ref("deltatech_partner_discount.group_partner_discount")
        self.user_with_discount = self.env["res.users"].create(
            {
                "name": "User With Discount",
                "login": "user_with_discount",
                "group_ids": [(6, 0, [self.discount_group.id])],
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

    def _allow_partner_edit(self, user):
        """Internal user allowed to edit contacts: only the discount group makes the difference."""
        user.group_ids = [(4, self.env.ref("base.group_user").id), (4, self.env.ref("base.group_partner_manager").id)]

    def test_write_discount_no_group_refused(self):
        """PARTNERDISC-001: a direct write (import / RPC) cannot bypass the onchange."""
        self._allow_partner_edit(self.user_no_discount)
        with self.assertRaisesRegex(UserError, "cannot modify the discount"):
            call_kw(
                self.env["res.partner"].with_user(self.user_no_discount),
                "write",
                [self.partner.ids, {"discount": 15.0}],
                {},
            )
        with self.assertRaisesRegex(UserError, "cannot modify the discount"):
            self.partner.with_user(self.user_no_discount).write({"discount": -5.0})
        self.assertEqual(self.partner.discount, 0.0)

    def test_write_other_fields_no_group_allowed(self):
        """Without the group, other fields and an unchanged discount can still be written."""
        self.partner.discount = 10.0
        self._allow_partner_edit(self.user_no_discount)
        partner = self.partner.with_user(self.user_no_discount)
        partner.write({"phone": "0700000000", "discount": 10.0})
        self.assertEqual(self.partner.phone, "0700000000")
        self.assertEqual(self.partner.discount, 10.0)

    def test_write_discount_with_group_allowed(self):
        self._allow_partner_edit(self.user_with_discount)
        call_kw(
            self.env["res.partner"].with_user(self.user_with_discount),
            "write",
            [self.partner.ids, {"discount": 12.0}],
            {},
        )
        self.assertEqual(self.partner.discount, 12.0)

    def test_write_discount_sudo_not_blocked(self):
        """Internal flows running as superuser are not blocked."""
        self.partner.with_user(self.user_no_discount).sudo().write({"discount": 7.0})
        self.assertEqual(self.partner.discount, 7.0)
