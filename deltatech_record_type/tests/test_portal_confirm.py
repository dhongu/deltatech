# ©  2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

from odoo import exceptions
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged("post_install", "-at_install")
class TestRecordTypeConfirm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_no_type = cls.env.ref("deltatech_record_type.group_confirm_order_without_record_type")
        # the setting "Confirm without order type" off: the group is not implied for all internal users
        cls.env.ref("base.group_user").implied_ids -= cls.group_no_type
        # an order type exists, so the type is required on confirmation
        cls.env["record.type"].create({"name": "Retail", "model": "sale.order"})
        cls.product = cls.env["product.product"].create({"name": "Test Product", "type": "service", "list_price": 10})
        cls.portal_user = new_test_user(cls.env, login="rt_portal", groups="base.group_portal")
        cls.salesman = new_test_user(cls.env, login="rt_salesman", groups="sales_team.group_sale_salesman_all_leads")
        cls.salesman.group_ids -= cls.group_no_type

    def _create_quotation(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.portal_user.partner_id.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1})],
            }
        )

    def test_portal_user_confirms_quotation_without_type(self):
        order = self._create_quotation()
        self.assertFalse(order.so_type)
        # same call as portal_quote_accept: sudo record, but env.user stays the portal user
        order.with_user(self.portal_user).sudo().with_context(sale_include_signature=True)._validate_order()
        self.assertEqual(order.state, "sale")

    def test_public_user_confirms_quotation_without_type(self):
        order = self._create_quotation()
        order.with_user(self.env.ref("base.public_user")).sudo()._validate_order()
        self.assertEqual(order.state, "sale")

    def test_payment_confirms_quotation_without_type(self):
        order = self._create_quotation()
        # confirmed by the payment only when the quotation does not have to be signed
        order.write({"require_signature": False, "prepayment_percent": 1.0})
        provider = self.env["payment.provider"].create({"name": "Test", "code": "none"})
        payment_method = self.env["payment.method"].create(
            {"name": "Test", "code": "rt_test", "provider_id": provider.id}
        )
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": provider.id,
                "payment_method_id": payment_method.id,
                "amount": order.amount_total,
                "currency_id": order.currency_id.id,
                "partner_id": order.partner_id.id,
                "sale_order_ids": [(6, 0, order.ids)],
                "state": "done",
            }
        )
        # an internal user without the exception group triggers the post-processing from the backend
        tx.with_user(self.salesman).sudo()._check_amount_and_confirm_order()
        self.assertEqual(order.state, "sale")

    def test_internal_user_without_group_is_blocked(self):
        order = self._create_quotation()
        with self.assertRaises(exceptions.UserError):
            order.with_user(self.salesman).action_confirm()
        # also in sudo: the user is still the internal one
        with self.assertRaises(exceptions.UserError):
            order.with_user(self.salesman).sudo().action_confirm()
        self.assertIn(order.state, ("draft", "sent"))

    def test_internal_user_with_group_confirms(self):
        self.salesman.group_ids |= self.group_no_type
        order = self._create_quotation()
        order.with_user(self.salesman).action_confirm()
        self.assertEqual(order.state, "sale")
