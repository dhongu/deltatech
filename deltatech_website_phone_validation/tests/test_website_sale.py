# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged

from odoo.addons.http_routing.tests.common import MockRequest

from ..controllers.website_sale import WebsiteSalePhoneValidation


@tagged("post_install", "-at_install")
class TestWebsiteSalePhoneValidation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.controller = WebsiteSalePhoneValidation()
        self.country_ro = self.env.ref("base.ro")

    def test_01_phone_validation_formatting(self):
        address_values = {
            "phone": " 0722123456 ",
            "country_id": self.country_ro.id,
        }
        # MockRequest is needed because the controller uses request.env
        with MockRequest(self.env):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values,
                partner_sudo=self.env.user.partner_id,
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="phone",
                is_main_address=True,
            )

            # Verificăm dacă telefonul a fost curățat de spații și formatat internațional
            # Pentru România (+40), 0722123456 devine +40 722 123 456
            self.assertEqual(address_values["phone"].replace(" ", ""), "+40722123456")
            self.assertNotIn("phone", invalid_fields)

    def test_02_phone_validation_invalid(self):
        address_values = {
            "phone": "invalid_phone",
            "country_id": self.country_ro.id,
        }
        with MockRequest(self.env):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values,
                partner_sudo=self.env.user.partner_id,
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="phone",
                is_main_address=True,
            )

            self.assertIn("phone", invalid_fields)
            self.assertTrue(error_messages)
