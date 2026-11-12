# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import json

from odoo.tests import tagged

from odoo.addons.deltatech_website_checkout_company.controllers.main import TbWebsiteSale
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon

from .test_checkout_company import VALID_CUI


@tagged("post_install", "-at_install")
class TestCheckoutCompanyController(WebsiteSaleCommon):
    """The address form submitted by a visitor, through the controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"].sudo()
        cls.Partner.search([("vat", "in", [VALID_CUI, f"RO{VALID_CUI}"])]).action_archive()
        cls.romania = cls.env.ref("base.ro")
        cls.county = cls.env["res.country.state"].search([("country_id", "=", cls.romania.id)], limit=1)
        cls.order = cls._create_so(partner_id=cls.website.user_id.partner_id.id)

    def setUp(self):
        super().setUp()
        self.controller = TbWebsiteSale()
        self.form = {
            "partner_id": -1,
            "address_type": "delivery",
            "use_delivery_as_billing": "true",
            "tb_lastname": "Popescu",
            "tb_firstname": "Ion",
            "email": "ion@example.com",
            "phone": "0700000000",
            "country_id": str(self.romania.id),
            "state_id": str(self.county.id),
            "city": "Bacau",
            "zip": "600001",
            "street": "Str. Livrare 1",
            "tb_company": "true",
        }

    def _submit(self, **values):
        with self.mock_request(sale_order_id=self.order.id) as request:
            request.httprequest.method = "POST"
            result = self.controller.shop_address_submit(**{**self.form, **values})
            feedback = json.loads(result.get_data(as_text=True) if hasattr(result, "get_data") else result)
            return feedback, self.controller._prepare_checkout_page_values(self.order)

    def test_existing_company_is_invoiced_and_shown_on_the_checkout_page(self):
        existing = (
            self.env["res.partner"]
            .sudo()
            .create({"name": "Existing SRL", "vat": f"RO{VALID_CUI}", "street": "Str. Sediu 1", "city": "Iasi"})
        )
        feedback, page_values = self._submit(tb_company_name="Other name", tb_company_vat=VALID_CUI)
        self.assertNotIn("invalid_fields", feedback)
        customer = self.order.partner_id
        self.assertEqual(customer.name, "Popescu Ion")
        self.assertFalse(customer.parent_id)
        self.assertEqual(self.order.partner_invoice_id, existing)
        self.assertEqual(self.order.partner_shipping_id, customer)
        # Not one of the customer's addresses, the company is still offered (and selected),
        # otherwise the checkout cannot go on.
        self.assertIn(existing, page_values["billing_addresses"])

    def test_invalid_vat_is_refused(self):
        feedback, _page_values = self._submit(tb_company_name="Test SRL", tb_company_vat="18547291")
        self.assertIn("tb_company_vat", feedback["invalid_fields"])
        self.assertEqual(self.order.partner_id, self.website.user_id.partner_id)

    def test_new_company_needs_its_registered_office(self):
        feedback, _page_values = self._submit(tb_company_name="Test SRL", tb_company_vat=VALID_CUI)
        self.assertTrue(
            {"tb_company_city", "tb_company_street"} <= set(feedback["invalid_fields"]),
            feedback,
        )
