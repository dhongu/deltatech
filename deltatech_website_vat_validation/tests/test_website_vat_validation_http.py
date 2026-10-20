# ©  2008-2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestWebsiteVatValidationHttp(HttpCase, WebsiteSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_ro = cls.env.ref("base.ro")
        cls.env["res.partner"].create(
            {"name": "Firma Existenta SRL", "vat": "RO12345607", "country_id": cls.country_ro.id}
        )
        cls.portal_user = new_test_user(cls.env, login="dt_vat_portal", groups="base.group_portal", name="Portal VAT")
        cls.portal_user.partner_id.write(cls.dummy_partner_address_values)
        cls.website.company_id.country_id = cls.country_ro

    def _add_to_cart(self):
        self.make_jsonrpc_request(
            "/shop/cart/add",
            {"product_template_id": self.product.product_tmpl_id.id, "product_id": self.product.id, "quantity": 1},
        )

    def test_address_form_public_visitor(self):
        self._add_to_cart()
        response = self.url_open("/shop/address")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="country_id"', response.text)

    def test_address_form_portal_user(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        self._add_to_cart()
        response = self.url_open("/shop/address")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="country_id"', response.text)

    def _submit(self, **values):
        return self.url_open(
            "/shop/address/submit",
            data={
                **self.dummy_partner_address_values,
                "name": self.portal_user.partner_id.name,
                "partner_id": self.portal_user.partner_id.id,
                "address_type": "billing",
                "csrf_token": self.csrf_token(),
                **values,
            },
        ).json()

    def test_submit_duplicate_vat_portal_user(self):
        """A customer cannot take over the tax code of another company (with or without prefix)."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        self._add_to_cart()
        for vat in ("RO12345607", "12345607", " ro 12345607 "):
            result = self._submit(vat=vat, country_id=self.country_ro.id, state_id="")
            self.assertIn("vat", result.get("invalid_fields", []), vat)
