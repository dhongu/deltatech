# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import json

from odoo.tests import tagged

from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon

from ..controllers.website_sale import WebsiteSaleVATValidation

VAT = "RO18547290"


@tagged("post_install", "-at_install")
class TestCompanyCreation(WebsiteSaleCommon):
    """A person who types a company name and a tax code in the billing address."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.partner"].search([("vat", "ilike", "18547290")]).action_archive()
        cls.romania = cls.env.ref("base.ro")

    def setUp(self):
        super().setUp()
        self.controller = WebsiteSaleVATValidation()
        self.customer = self.env.user.partner_id
        self.customer.write({"parent_id": False, "is_company": False, "vat": False, "company_name": False})
        self.order = self._create_so(partner_id=self.customer.id)
        self.form = {
            "partner_id": str(self.customer.id),
            "address_type": "billing",
            "name": "Popescu Ion",
            "email": "ion@example.com",
            "phone": "+40740123456",
            "street": "Str. Sediu 2",
            "city": "Craiova",
            "zip": "200001",
            "country_id": str(self.romania.id),
            "company_name": "Test Agro SRL",
            "vat": VAT,
        }

    def _submit(self, **changes):
        with MockRequest(self.env, website=self.website, sale_order_id=self.order.id) as request:
            request.httprequest.method = "POST"
            result = self.controller.shop_address_submit(**dict(self.form, **changes))
        result = result.get_data(as_text=True) if hasattr(result, "get_data") else result
        return json.loads(result)

    def test_company_is_created_and_the_person_becomes_its_contact(self):
        feedback = self._submit()
        self.assertNotIn("invalid_fields", feedback, feedback)
        company = self.customer.parent_id
        self.assertRecordValues(
            company,
            [
                {
                    "name": "Test Agro SRL",
                    "is_company": True,
                    "vat": VAT,
                    "street": "Str. Sediu 2",
                    "city": "Craiova",
                    "country_id": self.romania.id,
                }
            ],
        )
        self.assertRecordValues(self.customer, [{"company_name": False, "commercial_partner_id": company.id}])
        self.assertEqual(self.order.partner_invoice_id.commercial_partner_id, company)

    def test_no_company_without_a_company_name(self):
        feedback = self._submit(company_name="")
        self.assertNotIn("invalid_fields", feedback, feedback)
        self.assertFalse(self.customer.parent_id)
        self.assertEqual(self.customer.vat, VAT)

    def test_tax_code_of_another_customer_is_refused(self):
        existing = self.env["res.partner"].create({"name": "Existing SRL", "is_company": True, "vat": VAT})
        feedback = self._submit()
        self.assertIn("vat", feedback["invalid_fields"])
        self.assertFalse(self.customer.parent_id)
        self.assertNotEqual(self.order.partner_invoice_id.commercial_partner_id, existing)

    def test_customer_of_a_company_is_left_as_it_is(self):
        company = self.env["res.partner"].create({"name": "Own SRL", "is_company": True})
        self.customer.parent_id = company
        self._submit(company_name="Other SRL")
        self.assertEqual(self.customer.parent_id, company)
        self.assertEqual(self.env["res.partner"].search_count([("name", "=", "Other SRL")]), 0)

    def test_visitor_with_the_tax_code_of_a_customer_is_not_attached(self):
        existing = self.env["res.partner"].create({"name": "Existing SRL", "is_company": True, "vat": VAT})
        partner = self.env["res.partner"].create(
            {"name": "Guest", "company_name": "Existing SRL", "vat": VAT, "country_id": self.romania.id}
        )
        with MockRequest(self.env, website=self.website):
            self.controller._create_customer_company(partner.sudo())
        self.assertFalse(partner.parent_id)
        self.assertEqual(existing.child_ids, self.env["res.partner"])
