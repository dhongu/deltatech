# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestDisplayName(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_phone = cls.env["res.partner"].create({"name": "Contact Phone", "phone": "0722000000"})
        cls.partner_no_phone = cls.env["res.partner"].create({"name": "Contact No Phone"})

    def test_show_phone_with_phone(self):
        partner = self.partner_phone.with_context(show_phone=True)
        self.assertEqual(partner.display_name, "Contact Phone\n<0722000000>")

    def test_show_phone_without_phone(self):
        partner = self.partner_no_phone.with_context(show_phone=True)
        self.assertEqual(partner.display_name, "Contact No Phone")

    def test_without_context(self):
        self.assertEqual(self.partner_phone.display_name, "Contact Phone")
