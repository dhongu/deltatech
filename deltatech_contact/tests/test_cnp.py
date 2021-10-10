# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestCNP(TransactionCase):
    def setUp(self):
        super(TestCNP, self).setUp()

    def test_create_partner(self):
        form_partner = Form(self.env["res.partner"])
        form_partner.name = "Test"
        form_partner.is_company = False
        form_partner.birthdate = fields.Date.today()
        form_partner.cnp = "5000101015977"
        form_partner.save()

    def test_search_partner(self):
        values = {"name": "Test 2", "is_company": True, "vat": "RO20603502"}
        self.env["res.partner"].create(values)

        partner = self.env["res.partner"].name_search("20603502")
        self.assertEqual(partner[0][1], "Test 2")
