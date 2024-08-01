from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a partner
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "gln": "1234567890",
            }
        )

    def test_check_gln(self):
        # Check if the GLN is correctly set
        self.assertEqual(self.partner.gln, "1234567890", "GLN is not correctly set")
