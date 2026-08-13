# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged

from odoo.addons.http_routing.tests.common import MockRequest

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
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),  # Nou partener
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
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
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="email",
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
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="phone",
            )

            self.assertIn("phone", invalid_fields)
            self.assertTrue(any("already exists" in msg for msg in error_messages))

    def test_04_anaf_integration(self):
        # Simulăm datele ANAF folosind contextul, așa cum am văzut în l10n_ro_partner_create_by_vat/models/res_partner.py:_get_Anaf
        anaf_data = {
            "123456": {
                "date_generale": {
                    "denumire": "COMPANIA TEST ANAF SRL",
                    "cui": "123456",
                    "adresa": "STR. TEST NR. 1",
                },
                "adresa_sediu_social": {
                    "sdenumire_Strada": "TEST",
                    "snumar_Strada": "1",
                    "sdenumire_Localitate": "BUCURESTI",
                    "sdenumire_Judet": "BUCURESTI",
                    "scod_JudetAuto": "B",
                },
                "adresa_domiciliu_fiscal": {
                    "ddenumire_Strada": "TEST",
                    "dnumar_Strada": "1",
                    "ddenumire_Localitate": "BUCURESTI",
                    "ddenumire_Judet": "BUCURESTI",
                    "dcod_JudetAuto": "B",
                    "adresa": "STR. TEST NR. 1",
                },
            }
        }
        address_values = {
            "vat": "RO123456",
            "country_id": self.country_ro.id,
        }
        # Trebuie să ne asigurăm că metodele ANAF există pe res.partner (adică modulul e instalat)
        if not hasattr(self.env["res.partner"], "_get_Anaf"):
            self.skipTest("Modulul l10n_ro_partner_create_by_vat nu este instalat.")

        with MockRequest(self.env.with_context(anaf_data=anaf_data)):
            # Ne asigurăm că adresa este pentru România
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
            )

            self.assertEqual(address_values.get("name"), "COMPANIA TEST ANAF SRL")
            self.assertEqual(address_values.get("city"), "Bucuresti")
            self.assertEqual(address_values.get("street"), "Test Nr. 1")
            self.assertTrue(address_values.get("is_company"))
