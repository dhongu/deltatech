from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleOrderPaymentInvoice(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        # produs fara cost: vanzarea sub pretul de achizitie e blocata de deltatech_sale_margin
        cls.product_a.standard_price = 0.0
        cls.provider = cls.env["payment.provider"].create({"name": "Provider Without Journal", "code": "none"})
        # in 20 the "unknown" payment method is per provider (payment.payment_method_unknown is gone)
        cls.payment_method = cls.env["payment.method"].create(
            {"name": "Unknown", "code": "unknown", "provider_id": cls.provider.id}
        )
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


@tagged("post_install", "-at_install")
class TestSaleOrderPaymentForeignCurrency(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        # produs fara cost: vanzarea sub pretul de achizitie e blocata de deltatech_sale_margin
        cls.product_a.standard_price = 0.0
        # comanda in valuta, factura emisa la cursul 5 (100 valuta = 500 in moneda companiei)
        cls.other_currency = cls.setup_other_currency("EUR", rates=[("2016-01-01", 0.2)])
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "EUR pricelist", "currency_id": cls.other_currency.id}
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "pricelist_id": cls.pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {"product_id": cls.product_a.id, "product_uom_qty": 1.0, "price_unit": 100.0, "tax_ids": False},
                    )
                ],
            }
        )
        cls.sale_order.action_confirm()
        cls.invoice = cls.sale_order._create_invoices()
        cls.invoice.invoice_date = "2017-01-01"
        cls.invoice.action_post()

    def _pay_invoice(self, amount):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=self.invoice.ids
        ).create(
            {
                "amount": amount,
                "currency_id": self.other_currency.id,
                "journal_id": self.company_data["default_journal_bank"].id,
            }
        )._create_payments()
        self.sale_order.invalidate_recordset(["payment_amount", "payment_status"])

    def test_partial_payment_in_order_currency(self):
        # SALEPAY-001: 50 platiti din 100 nu inseamna comanda platita (250 in moneda companiei >= 100)
        self.assertEqual(self.sale_order.currency_id, self.other_currency)
        self.assertEqual(self.invoice.amount_total_signed, 500.0)
        self._pay_invoice(50.0)
        self.assertEqual(self.sale_order.payment_amount, 50.0)
        self.assertEqual(self.sale_order.payment_status, "partial")
        self.assertEqual(max(0.0, self.sale_order.amount_total - self.sale_order.payment_amount), 50.0)

    def test_full_payment_in_order_currency(self):
        self._pay_invoice(100.0)
        self.assertEqual(self.sale_order.payment_amount, 100.0)
        self.assertEqual(self.sale_order.payment_status, "done")

    def test_refund_offsets_invoice(self):
        # factura stornata integral: nota de credit se reconciliaza cu factura, nu s-a incasat nimic
        self.invoice._reverse_moves(cancel=True)
        self.sale_order.invalidate_recordset(["payment_amount", "payment_status"])
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        self.assertEqual(self.sale_order.payment_status, "without")
