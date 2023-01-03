from odoo.tests.common import TransactionCase


class TestAccountMove(TransactionCase):
    def test_open_payments(self):
        # se va adauga un partener
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        # se va crea o factura
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test",
                            "quantity": 1,
                            "price_unit": 100,
                            "account_id": self.env.ref("account.data_account_type_revenue").id,
                        },
                    )
                ],
            }
        )
        # se posteaza factura
        invoice.action_post()

        # se va crea o plata pentru factura inregistrata
        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner.id,
                "amount": 100,
                "payment_method_id": self.env.ref("account.account_payment_method_manual_in").id,
            }
        )
        # se posteaza plata
        payment.action_post()

        # se va reconcilia factura cu plata
        payment.move_line_ids[0].reconcile(
            invoice.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ("receivable", "payable"))
        )

        # se deschide plata
        action = invoice.open_payments()

        # se verifica daca s-a deschis o fereastra cu plata
        self.assertEqual(action["res_id"], payment.id)
