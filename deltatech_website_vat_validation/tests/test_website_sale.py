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
                "vat": "RO12345607",
                "email": "existing@example.com",
                "phone": "+40711111111",
                "country_id": self.country_ro.id,
            }
        )

    def test_01_vat_uniqueness(self):
        address_values = {
            "name": "New Partner",
            "vat": " RO12345607 ",  # Cu spații pentru a testa și striping
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
            self.assertTrue(any("already has an account" in msg for msg in error_messages))
            self.assertFalse(any("Existing Partner" in msg for msg in error_messages), "the account is not named")

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
            self.assertTrue(any("belongs to another account" in msg for msg in error_messages))

    def test_03_phone_shared_is_accepted(self):
        """Colleagues share the company phone, relatives a home phone: not a duplicate."""
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

            self.assertNotIn("phone", invalid_fields)

    def test_05_public_user_no_enumeration(self):
        public_user = self.env.ref("base.public_user")
        for field, value in [
            ("email", "existing@example.com"),
            ("phone", "+40711111111"),
            ("vat", "RO12345607"),
        ]:
            address_values = {"name": "Guest", field: value, "country_id": self.country_ro.id}
            with MockRequest(self.env(user=public_user)):
                invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                    address_values=address_values,
                    partner_sudo=self.env["res.partner"].sudo(),
                    address_type="delivery",
                    use_delivery_as_billing=False,
                    required_fields=field,
                )
            self.assertNotIn(field, invalid_fields)
            self.assertFalse(any("already exists" in msg for msg in error_messages))
            self.assertFalse(any(value in msg for msg in error_messages))

    def _validate_vat_as(self, vat, partner_sudo=None):
        with MockRequest(self.env):
            return self.controller._validate_address_values(
                address_values={"name": "Contact", "vat": vat, "country_id": self.country_ro.id},
                partner_sudo=partner_sudo or self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
            )

    def test_11_vat_duplicate_with_or_without_prefix(self):
        self.env["res.partner"].create(
            {"name": "Firma Existenta SRL", "vat": "RO1234567897", "country_id": self.country_ro.id}
        )
        invalid_fields, _missing, error_messages = self._validate_vat_as("1234567897")
        self.assertIn("vat", invalid_fields)
        if "b2b_state" in self.env["res.partner"]._fields:
            self.assertTrue(any("/b2b" in msg for msg in error_messages), "the access request form is offered")
        else:
            self.assertTrue(any("contact us" in msg for msg in error_messages))

    def test_12_own_company_vat_is_not_a_duplicate(self):
        """A contact of a company who types the tax code of their own company is not blocked."""
        company = self.env["res.partner"].create(
            {"name": "Firma Mea SRL", "vat": "RO1234567897", "country_id": self.country_ro.id}
        )
        contact = self.env["res.partner"].create({"name": "Coleg", "parent_id": company.id, "type": "invoice"})
        invalid_fields, _missing, error_messages = self._validate_vat_as("RO1234567897", partner_sudo=contact.sudo())
        self.assertNotIn("vat", invalid_fields)
        self.assertFalse(any("already has an account" in msg for msg in error_messages))
