# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestAgreement(TransactionCase):
    def setUp(self):
        super(TestAgreement, self).setUp()
        self.partner_1 = self.env["res.partner"].create({"name": "Test Partner"})
        self.product_1 = self.env["product.product"].create({"name": "Test Product"})

        self.journal = self.env["account.journal"].create(
            {
                "name": "Test Journal",
                "type": "sale",
                "code": "TEST",
                "service_invoice": True,
            }
        )

        self.agreement_type = self.env["service.agreement.type"].create(
            {
                "name": "Test Agreement Type",
                "journal_id": self.journal.id,
            }
        )
        self.cycle = self.env["service.cycle"].create(
            {
                "name": "Test Cycle",
                "value": 1,
                "unit": "month",
            }
        )

    def test_agreement(self):
        agreement = Form(self.env["service.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle

        agreement_line = agreement.agreement_line.new()
        agreement_line.product_id = self.product_1
        agreement_line.quantity = 1
        agreement_line.price_unit = 100

        agreement = agreement.save()

        # consumption = Form(self.env["service.consumption"])
        # consumption.agreement_id = agreement
        # consumption.agreement_line_id = agreement.agreement_line
        # consumption.quantity = 1
