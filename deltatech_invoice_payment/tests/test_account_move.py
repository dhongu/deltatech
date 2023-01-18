from odoo.tests import Form
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
        payment_register = self.env["account.payment.register"]
        payment_register = payment_register.with_context(active_model="account.move", active_ids=invoice.ids)
        payment_form = Form(payment_register)
        payment = payment_form.save()
        payment.action_create_payments()

        # se deschide plata
        action = invoice.open_payments()

        # se verifica daca s-a deschis o fereastra cu plata
        self.assertEqual(action["res_id"], payment.id)
