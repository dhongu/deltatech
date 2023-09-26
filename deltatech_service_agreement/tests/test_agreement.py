# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestAgreement(TransactionCase):
    def setUp(self):
        super().setUp()
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
        self.env["service.date.range"].generate_date_range()
        self.date_range = self.env["service.date.range"].search([], limit=1)

    def test_agreement(self):
        agreement = Form(self.env["service.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle

        with agreement.agreement_line.new() as agreement_line:
            agreement_line.product_id = self.product_1
            agreement_line.quantity = 1
            agreement_line.price_unit = 100

        agreement = agreement.save()
        agreement.contract_open()

        wizard = Form(self.env["service.billing.preparation"].with_context(active_ids=[agreement.id]))
        wizard.service_period_id = self.date_range
        wizard = wizard.save()
        action = wizard.do_billing_preparation()

        consumptions = self.env["service.consumption"].search(action["domain"])

        wizard = Form(self.env["service.distribution"].with_context(active_ids=consumptions.ids))
        wizard.quantity = 10
        wizard = wizard.save()
        wizard.do_distribution()

        wizard = Form(self.env["service.price.change"].with_context(active_ids=consumptions.ids))
        wizard.price_unit = 5
        wizard = wizard.save()
        wizard.do_price_change()

        wizard = Form(self.env["service.billing"].with_context(active_ids=consumptions.ids))
        wizard = wizard.save()
        action = wizard.do_billing()

        invoices = self.env["account.move"].search(action["domain"])
        invoices.action_post()
