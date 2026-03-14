# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged

from odoo.addons.website.tools import MockRequest

from ..controllers.website_sale import WebsiteSaleVATValidation


@tagged("post_install", "-at_install")
class TestWebsiteSaleVATValidation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.controller = WebsiteSaleVATValidation()
        self.country_ro = self.env.ref("base.ro")

        # Creăm un partener existent pentru teste de unicitate
        self.existing_partner = self.env["res.partner"].create(
            {
                "name": "Existing Partner",
                "vat": "RO8001011234567",
                "email": "existing@example.com",
                "phone": "+40711111111",
                "country_id": self.country_ro.id,
            }
        )

    def test_01_vat_uniqueness(self):
        address_values = {
            "name": "New Partner",
            "vat": " RO8001011234567 ",  # Cu spații pentru a testa și striping
            "country_id": self.country_ro.id,
        }
        with MockRequest(self.env):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values,
                partner_sudo=self.env["res.partner"].sudo(),  # Nou partener
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
                is_main_address=True,
            )

            self.assertIn("vat", invalid_fields)
            self.assertTrue(any("already exists" in msg for msg in error_messages))

    def test_02_email_uniqueness(self):
        address_values = {
            "name": "New Partner",
            "email": " existing@example.com ",
            "country_id": self.country_ro.id,
        }
        with MockRequest(self.env):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="email",
                is_main_address=True,
            )

            self.assertIn("email", invalid_fields)
            self.assertTrue(any("already exists" in msg for msg in error_messages))

    def test_03_phone_uniqueness(self):
        # Pentru telefon, validarea unicității se face după striping în deltatech_website_vat_validation
        # Dar atenție, phone_validation poate formata numărul în super()
        address_values = {
            "name": "New Partner",
            "phone": " +40711111111 ",
            "country_id": self.country_ro.id,
        }
        with MockRequest(self.env):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="phone",
                is_main_address=True,
            )

            self.assertIn("phone", invalid_fields)
            self.assertTrue(any("already exists" in msg for msg in error_messages))
