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


class TestGetNameOnly(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Partner = cls.env["res.partner"]
        cls.company = Partner.create({"name": "Agro Prod SRL", "is_company": True})
        cls.person = Partner.create({"name": "Andrei Popescu", "parent_id": cls.company.id, "type": "contact"})
        cls.address = Partner.create({"name": "Depozit", "parent_id": cls.company.id, "type": "delivery"})

    def test_param_off(self):
        self.assertEqual(self.person.display_name, "Agro Prod SRL, Andrei Popescu")

    def test_param_on(self):
        self.env["ir.config_parameter"].sudo().set_param("contact.get_name_only", "1")
        self.person.invalidate_recordset()
        self.assertEqual(self.person.display_name, "Andrei Popescu")
        # other address types keep the company
        self.address.invalidate_recordset()
        self.assertEqual(self.address.display_name, "Agro Prod SRL, Depozit")
        # company itself unchanged
        self.assertEqual(self.company.display_name, "Agro Prod SRL")
