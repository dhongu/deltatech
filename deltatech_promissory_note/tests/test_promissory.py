# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPromissoryNote(TransactionCase):
    def setUp(self):
        super(TestPromissoryNote, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "TestA"})
        self.partner_b = self.env["res.partner"].create({"name": "TestB"})

    def test_promissory_note_vendor(self):

        promissory_note = Form(self.env["promissory.note"])
        promissory_note.name = "Test"
        promissory_note.date_due = "2020-03-18"
        promissory_note.type = "vendor"
        promissory_note.beneficiary_id = self.partner_b
        promissory_note.amount = 1000
        promissory_note.currency_id = self.env.ref("base.EUR")
        promissory_note.acc_issuer = "XXX"
        promissory_note.acc_beneficiary = "XXX"
        promissory_note.bank_issuer = "XXX"
        promissory_note.bank_beneficiary = "XXX"
        promissory_note.is_last_bo = True
        promissory_note = promissory_note.save()
        promissory_note.action_cashed()

    def test_promissory_note_customer(self):

        promissory_note = Form(self.env["promissory.note"])
        promissory_note.name = "Test"
        promissory_note.date_due = "2020-03-18"
        promissory_note.type = "customer"
        promissory_note.issuer_id = self.partner_a
        promissory_note.amount = 1000
        promissory_note.currency_id = self.env.ref("base.EUR")
        promissory_note.acc_issuer = "XXX"
        promissory_note.acc_beneficiary = "XXX"
        promissory_note.bank_issuer = "XXX"
        promissory_note.bank_beneficiary = "XXX"
        promissory_note.is_last_bo = True
        promissory_note = promissory_note.save()
        promissory_note.action_cashed()
