# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPayment(TransactionCase):
    def setUp(self):
        super(TestPayment, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "test"})

    def test_payment(self):

        cash_journal = self.env["account.journal"].search([("type", "=", "cash")], limit=1)

        payment_1 = self.env["account.payment"].create(
            {
                "amount": 150.0,
                "payment_type": "inbound",
                "partner_type": "customer",
                "date": "2015-01-01",
                "journal_id": cash_journal.id,
                "partner_id": self.partner_a.id,
                "payment_method_id": self.env.ref("account.account_payment_method_manual_in").id,
            }
        )

        payment_2 = self.env["account.payment"].create(
            {
                "amount": 250.0,
                "payment_type": "outbound",
                "partner_type": "supplier",
                "date": "2015-01-02",
                "journal_id": cash_journal.id,
                "partner_id": self.partner_a.id,
                "payment_method_id": self.env.ref("account.account_payment_method_manual_out").id,
            }
        )

        payment_1.action_post()
        payment_2.action_post()

        cash_journal.get_journal_dashboard_datas()

    def test_payment_date_journal(self):
        cash_journal = self.env["account.journal"].search([("type", "=", "cash")], limit=1)
        payment_3 = self.env["account.payment"].create(
            {
                "amount": 150.0,
                "payment_type": "inbound",
                "partner_type": "customer",
                "date": "2015-02-02",
                "journal_id": cash_journal.id,
                "partner_id": self.partner_a.id,
                "payment_method_id": self.env.ref("account.account_payment_method_manual_in").id,
            }
        )
        payment_form = Form(payment_3)
        payment_form.date = "2015-02-02"
