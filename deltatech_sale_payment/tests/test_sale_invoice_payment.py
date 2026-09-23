from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleOrderPaymentInvoice(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id |= cls.env.ref("sales_team.group_sale_manager")
        cls.provider = cls.env["payment.provider"].create({"name": "Provider Without Journal", "code": "none"})
        cls.payment_method = cls.env.ref("payment.payment_method_unknown")
        # the suite may forbid selling below cost (deltatech_sale_margin); keep the order at a profit
        cls.product_a.standard_price = 0.0
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "order_line": [(0, 0, {"product_id": cls.product_a.id, "product_uom_qty": 1.0, "price_unit": 100.0})],
            }
        )
        cls.sale_order.action_confirm()
        cls.invoice = cls.sale_order._create_invoices()
        cls.invoice.action_post()

    def _create_transaction(self, amount, payment=None):
        tx = (
            self.env["payment.transaction"]
            .sudo()
            .create(
                {
                    "provider_id": self.provider.id,
                    "payment_method_id": self.payment_method.id,
                    "reference": f"TX-{self.sale_order.name}-{len(self.sale_order.transaction_ids)}",
                    "amount": amount,
                    "currency_id": self.sale_order.currency_id.id,
                    "partner_id": self.partner_a.id,
                    "state": "done",
                    "is_post_processed": True,
                    "payment_id": payment and payment.id,
                    "sale_order_ids": [(4, self.sale_order.id)],
                    "invoice_ids": [(4, self.invoice.id)],
                }
            )
        )
        return tx

    def test_invoice_partial_payment_keeps_transaction_without_payment(self):
        # Tranzactia initiala e confirmata pe un provider fara jurnal (fara plata contabila),
        # iar diferenta se incaseaza printr-o tranzactie care genereaza plata pe factura.
        # Suma incasata pe factura nu trebuie sa ascunda tranzactia fara plata.
        self._create_transaction(self.sale_order.amount_total - 40.0)
        payment = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=self.invoice.ids)
            .create({"amount": 40.0, "journal_id": self.company_data["default_journal_bank"].id})
            ._create_payments()
        )
        self._create_transaction(40.0, payment=payment)
        self.assertEqual(self.invoice.amount_residual, self.invoice.amount_total - 40.0)

        self.sale_order.invalidate_recordset(["payment_amount", "payment_status"])
        self.assertEqual(self.sale_order.payment_amount, self.sale_order.amount_total)
        self.assertEqual(self.sale_order.payment_status, "done")

    def test_invoice_paid_by_transaction_is_not_counted_twice(self):
        # Tranzactia care a generat plata pe factura e deja inclusa in suma incasata a facturii.
        payment = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=self.invoice.ids)
            .create({"amount": 40.0, "journal_id": self.company_data["default_journal_bank"].id})
            ._create_payments()
        )
        self._create_transaction(40.0, payment=payment)

        self.sale_order.invalidate_recordset(["payment_amount", "payment_status"])
        self.assertEqual(self.sale_order.payment_amount, 40.0)
        self.assertEqual(self.sale_order.payment_status, "partial")

    def test_settled_card_transaction_is_not_counted_twice(self):
        # Tranzactia pe card (fara plata contabila) acopera toata comanda; factura se inchide
        # ulterior din extrasul bancar al procesatorului, printr-o plata care nu e legata de
        # tranzactie. Sunt aceiasi bani: suma incasata nu trebuie sa fie dublul totalului.
        self._create_transaction(self.sale_order.amount_total)
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=self.invoice.ids
        ).create({"journal_id": self.company_data["default_journal_bank"].id})._create_payments()
        self.assertFalse(self.invoice.amount_residual)

        self.sale_order.invalidate_recordset(["payment_amount", "payment_status"])
        self.assertEqual(self.sale_order.payment_amount, self.sale_order.amount_total)
        self.assertEqual(self.sale_order.payment_status, "done")
