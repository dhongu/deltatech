# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestAgreement(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_1 = self.env["res.partner"].create({"name": "Test Partner"})
        # self.product_1 = self.env["product.product"].create({"name": "Test Product"})
        self.agreement_type = self.env["general.agreement.type"].create({"name": "Test Agreement Type"})

    def test_create_agreement(self):
        agreement = Form(self.env["general.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement = agreement.save()
        self.assertEqual(agreement.state, "draft")

    def test_agreement_flow(self):
        sequence = self.env["ir.sequence"].create({"name": "Agreement", "prefix": "AGR/", "padding": 3})
        self.agreement_type.sequence_id = sequence
        agreement = self.env["general.agreement"].create(
            {"partner_id": self.partner_1.id, "type_id": self.agreement_type.id}
        )
        self.assertEqual(agreement.name, "/")
        agreement.get_name()
        self.assertTrue(agreement.name.startswith("AGR/"))
        agreement.contract_open()
        self.assertEqual(agreement.state, "open")
        with self.assertRaises(UserError):
            agreement.unlink()
        with self.assertRaises(UserError):
            agreement.print_agreement()
        agreement.contract_close()
        self.assertEqual(agreement.state, "closed")
        agreement.contract_draft()
        self.assertEqual(agreement.state, "draft")

        self.assertEqual(self.partner_1.agreement_count, 1)
        partners = self.env["res.partner"].search([("agreement_count", "!=", False)])
        self.assertIn(self.partner_1, partners)
        action = self.partner_1.view_agreements()
        self.assertEqual(action["res_model"], "general.agreement")

        agreement.unlink()
        self.assertFalse(agreement.exists())

    def test_get_name_without_sequence(self):
        agreement = self.env["general.agreement"].create({"type_id": self.agreement_type.id})
        with self.assertRaises(UserError):
            agreement.get_name()
