from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleContact(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parent_partner = cls.env["res.partner"].create(
            {
                # in 20.0 is_company is computed (own commercial entity + VAT)
                "name": "Parent Company",
            }
        )
        cls.contact_1 = cls.env["res.partner"].create(
            {
                "name": "Contact 1",
                "parent_id": cls.parent_partner.id,
                "type": "delivery",
            }
        )
        cls.contact_2 = cls.env["res.partner"].create(
            {
                "name": "Contact 2",
                "parent_id": cls.parent_partner.id,
                "type": "delivery",
            }
        )
        cls.invoice_contact = cls.env["res.partner"].create(
            {
                "name": "Invoice Contact",
                "parent_id": cls.parent_partner.id,
                "type": "invoice",
            }
        )

    def test_01_contact_default_uniqueness(self):
        """Test that setting contact_default to True unsets it for other contacts of the same type"""
        self.contact_1.write({"contact_default": True})
        self.assertTrue(self.contact_1.contact_default)

        self.contact_2.write({"contact_default": True})
        self.assertTrue(self.contact_2.contact_default)
        self.contact_1.invalidate_recordset(["contact_default"])
        self.assertFalse(self.contact_1.contact_default, "Contact 1 should no longer be default")

    def test_02_address_get_default(self):
        """Test that address_get returns the default contact"""
        self.contact_2.write({"contact_default": True})
        self.invoice_contact.write({"contact_default": True})

        addresses = self.parent_partner.address_get(["delivery", "invoice"])
        self.assertEqual(addresses["delivery"], self.contact_2.id)
        self.assertEqual(addresses["invoice"], self.invoice_contact.id)

    def test_03_sale_order_domains(self):
        """Test domains on sale.order"""
        # We can check domains by looking at the field definitions or using search with domains
        so_model = self.env["sale.order"]

        # Test partner_id domain (parent_id = False)
        domain_partner = so_model._fields["partner_id"].domain
        self.assertEqual(domain_partner, [("parent_id", "=", False)])

        # Test invoice and shipping domains
        # Note: These are strings in the model, so we check them as strings or eval them
        domain_invoice = so_model._fields["partner_invoice_id"].domain
        self.assertIn("partner_id", domain_invoice)
        self.assertIn("invoice", domain_invoice)

        domain_shipping = so_model._fields["partner_shipping_id"].domain
        self.assertIn("partner_id", domain_shipping)
        self.assertIn("delivery", domain_shipping)

    def test_04_account_move_domain(self):
        """Test domain on account.move"""
        move_model = self.env["account.move"]
        domain_partner = move_model._fields["partner_id"].domain
        self.assertEqual(domain_partner, [("parent_id", "=", False)])

    def test_05_address_get_without_preferences(self):
        """address_get must accept the default None preferences (e.g. event registration)"""
        self.contact_2.write({"contact_default": True})
        self.invoice_contact.write({"contact_default": True})
        standard = self.parent_partner.address_get(["contact"])
        for adr_pref in ((), (None,), ([],)):
            addresses = self.parent_partner.address_get(*adr_pref)
            self.assertEqual(addresses, standard)
        self.assertEqual(self.parent_partner.address_get(["delivery"])["delivery"], self.contact_2.id)
        self.assertEqual(self.parent_partner.address_get(["invoice"])["invoice"], self.invoice_contact.id)

    def test_06_contact_default_other_type_kept(self):
        """Setting a default delivery contact must not reset the default invoice contact"""
        self.invoice_contact.write({"contact_default": True})
        self.contact_1.write({"contact_default": True})
        self.invoice_contact.invalidate_recordset(["contact_default"])
        self.assertTrue(self.invoice_contact.contact_default)
        self.assertTrue(self.contact_1.contact_default)
        self.assertFalse(self.contact_2.contact_default)

    def test_07_address_get_without_default(self):
        """Without a default contact address_get keeps the standard behaviour"""
        addresses = self.parent_partner.address_get(["delivery", "invoice"])
        self.assertEqual(addresses["delivery"], self.contact_1.id)
        self.assertEqual(addresses["invoice"], self.invoice_contact.id)

    def test_08_print_green_invoice_field(self):
        """The green invoice flag is stored on the partner"""
        self.parent_partner.print_green_invoice = True
        self.assertTrue(self.parent_partner.print_green_invoice)
