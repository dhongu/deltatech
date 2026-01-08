from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleContact(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parent_partner = cls.env["res.partner"].create(
            {
                "name": "Parent Company",
                "is_company": True,
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
