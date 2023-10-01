# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestAgreement(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_1 = self.env["res.partner"].create({"name": "Test Partner"})
        self.product_1 = self.env["product.product"].create({"name": "Test Product"})
        self.agreement_type = self.env["general.agreement.type"].create({"name": "Test Agreement Type"})

    def test_create_agreement(self):
        agreement = Form(self.env["general.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type

        agreement = agreement.save()

        agreement.contract_open()
        # agreement.print_agreement()
        agreement.contract_close()
        agreement.contract_draft()
