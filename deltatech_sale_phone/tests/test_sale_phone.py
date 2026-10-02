from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPartnerPhone(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # The accounting test user lacks sales rights; grant them so we can
        # create sale orders.
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_salesman")

        # Partner with phone
        cls.partner_with_phone = cls.env["res.partner"].create(
            {
                "name": "Partner with Phone",
                "phone": "123-456-7890",
            }
        )

        # Partner without any contact details
        cls.partner_with_no_contact = cls.env["res.partner"].create(
            {
                "name": "Partner with No Contact",
            }
        )

        # Account move records
        cls.account_move_with_phone = cls.env["account.move"].create(
            {
                "partner_id": cls.partner_with_phone.id,
                "move_type": "out_invoice",
            }
        )
        cls.account_move_with_no_contact = cls.env["account.move"].create(
            {
                "partner_id": cls.partner_with_no_contact.id,
                "move_type": "out_invoice",
            }
        )

        # Sale order records
        cls.sale_order_with_phone = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_with_phone.id,
            }
        )
        cls.sale_order_with_no_contact = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_with_no_contact.id,
            }
        )

    def test_account_move_phone_computation(self):
        self.assertEqual(
            self.account_move_with_phone.partner_phone,
            "123-456-7890",
            "The phone should be set from the partner's phone.",
        )
        self.assertFalse(
            self.account_move_with_no_contact.partner_phone,
            "The phone should be False for a partner with no contact details.",
        )

    def test_sale_order_phone_computation(self):
        self.assertEqual(
            self.sale_order_with_phone.partner_phone,
            "123-456-7890",
            "The phone should be set from the partner's phone.",
        )
        self.assertFalse(
            self.sale_order_with_no_contact.partner_phone,
            "The phone should be False for a partner with no contact details.",
        )
