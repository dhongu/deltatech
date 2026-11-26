from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):
    """`gln` is a bridge to the standard `global_location_number`."""

    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Partner", "gln": "1234567890"})

    def test_check_gln(self):
        self.assertEqual(self.partner.gln, "1234567890", "GLN is not correctly set")

    def test_gln_writes_the_standard_field(self):
        self.assertEqual(self.partner.global_location_number, "1234567890")
        self.partner.gln = "5940000000017"
        self.assertEqual(self.partner.global_location_number, "5940000000017")

    def test_standard_field_is_read_through_gln(self):
        self.partner.global_location_number = "5940000000024"
        self.assertEqual(self.partner.gln, "5940000000024")

    def test_search_by_gln(self):
        self.partner.global_location_number = "5940000000031"
        found = self.env["res.partner"].search([("gln", "=", "5940000000031")])
        self.assertEqual(found, self.partner)

    def test_no_own_column(self):
        self.assertFalse(self.env["res.partner"]._fields["gln"].store)
