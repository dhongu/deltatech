# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestCNP(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_create_partner(self):
        form_partner = Form(self.env["res.partner"])
        form_partner.name = "Test"
        form_partner.birthdate = fields.Date.today()
        form_partner.cnp = "5000101015977"
        form_partner.save()

    def test_check_single_cnp(self):
        partner = self.env["res.partner"]
        cases = {
            "5000101015977": True,  # valid
            "": True,
            "   ": True,
            False: True,
            " 5000101015977 ": True,  # surrounding whitespace is stripped
            "A000101015977": False,  # non-digit first char
            "500010A015977": False,  # non-digit middle char
            "500010101597A": False,  # non-digit check digit
            "5000 01015977": False,  # inner separator
            "5²00101015977": False,  # Unicode digit rejected by int()
            "500010101597": False,  # too short
            "50001010159770": False,  # too long
            "5000101015978": False,  # wrong checksum
        }
        for cnp, expected in cases.items():
            with self.subTest(cnp=cnp):
                self.assertEqual(partner.check_single_cnp(cnp), expected)

    def test_create_invalid_cnp_is_cleared(self):
        for cnp in ("A234567890123", "5²00101015977", "5000101015978"):
            with self.subTest(cnp=cnp):
                partner = self.env["res.partner"].create({"name": "Test", "cnp": cnp})
                self.assertFalse(partner.cnp)

    def test_write_invalid_cnp_raises(self):
        partner = self.env["res.partner"].create({"name": "Test"})
        for cnp in ("A234567890123", "5²00101015977", "5000101015978"):
            with self.subTest(cnp=cnp), self.assertRaises(ValidationError):
                partner.write({"cnp": cnp})
        partner.write({"cnp": "5000101015977"})
        self.assertEqual(partner.cnp, "5000101015977")

    def test_onchange_nondigit_cnp(self):
        form_partner = Form(self.env["res.partner"])
        form_partner.name = "Test"
        form_partner.cnp = "A234567890123"  # must not raise in cnp_change
        form_partner.cnp = "5001301015977"  # month 13: must not raise
        form_partner.birthdate = fields.Date.today()  # birthdate_change on bad CNP
        form_partner.cnp = "5000101015977"
        self.assertEqual(str(form_partner.birthdate), "2000-01-01")

    def test_search_partner(self):
        values = {"name": "Test 2", "is_company": True, "vat": "RO20603502"}
        self.env["res.partner"].create(values)

        partner = self.env["res.partner"].name_search("20603502")
        self.assertEqual(partner[0][1], "Test 2")
