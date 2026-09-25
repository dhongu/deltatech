from unittest.mock import patch

from odoo import http
from odoo.tests import HttpCase, tagged

from odoo.addons.payment.tests.common import PaymentCommon


@tagged("post_install", "-at_install")
class TestCheckoutConfirm(PaymentCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].get_current_website()
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "list_price": 100.0, "sale_ok": True, "website_published": True}
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "website_id": cls.website.id,
                "order_line": [(0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})],
            }
        )

    def _open_confirmation(self):
        self.authenticate(None, None)
        self.session["sale_last_order_id"] = self.order.id
        http.root.session_store.save(self.session)
        response = self.url_open("/shop/confirmation")
        self.assertEqual(response.status_code, 200)
        return response

    def _create_tx(self, state, provider=None):
        return self._create_transaction(
            "redirect",
            state=state,
            provider_id=(provider or self.provider).id,
            amount=self.order.amount_total,
            currency_id=self.order.currency_id.id,
            partner_id=self.partner.id,
            sale_order_ids=[(6, 0, self.order.ids)],
        )

    def test_no_transaction_not_confirmed(self):
        self._open_confirmation()
        self.assertEqual(self.order.state, "draft")

    def test_pending_online_transaction_not_confirmed(self):
        self._create_tx("pending")
        self._open_confirmation()
        self.assertEqual(self.order.state, "draft")

    def test_done_transaction_confirmed(self):
        self._create_tx("done")
        self._open_confirmation()
        self.assertEqual(self.order.state, "sale")

    def test_pending_offline_transaction_confirmed(self):
        # Treat the test provider as offline (wire transfer / cash on delivery) without
        # depending on payment_custom or deltatech_payment_on_delivery.
        self._create_tx("pending")
        with patch(
            "odoo.addons.deltatech_website_checkout_confirm.controllers.website_sale.OFFLINE_PROVIDER_CODES",
            (self.provider.code,),
        ):
            self._open_confirmation()
        self.assertEqual(self.order.state, "sale")

    def test_reload_no_error(self):
        self._create_tx("done")
        self._open_confirmation()
        self.assertEqual(self.order.state, "sale")
        self._open_confirmation()
        self.assertEqual(self.order.state, "sale")
