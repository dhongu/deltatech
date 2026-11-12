# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import json

from odoo.tests import TransactionCase, tagged

from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon

from ..controllers.main import TbWebsiteSale

# A valid Romanian CUI (checksum included).
VALID_CUI = "18547290"


@tagged("post_install", "-at_install")
class TestCheckoutCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        # The tests start with no partner on the test CUI.
        cls.Partner.search([("vat", "in", [VALID_CUI, f"RO{VALID_CUI}"])]).action_archive()
        cls.customer = cls.Partner.create(
            {
                "name": "Popescu Ion",
                "email": "ion@example.com",
                "phone": "0700000000",
                "street": "Str. Livrare 1",
                "city": "Bacau",
                "country_id": cls.env.ref("base.ro").id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Part", "list_price": 10.0})
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "order_line": [(0, 0, {"product_id": cls.product.id})],
            }
        )
        cls.county = cls.env["res.country.state"].search([("country_id.code", "=", "RO")], limit=1)
        cls.office = {"state_id": cls.county.id, "city": "Craiova", "street": "Str. Sediu 2", "zip": "200001"}

    def test_clean_and_validate_vat(self):
        self.assertEqual(self.Partner._tb_clean_company_vat(" ro 18.547.290 "), "RO18547290")
        self.assertTrue(self.Partner._tb_is_valid_company_vat(VALID_CUI))
        self.assertTrue(self.Partner._tb_is_valid_company_vat(f"RO{VALID_CUI}"))
        self.assertFalse(self.Partner._tb_is_valid_company_vat("18547291"))
        self.assertFalse(self.Partner._tb_is_valid_company_vat(""))

    def test_new_company_is_created_and_customer_becomes_its_delivery_address(self):
        company = self.order._tb_prepare_invoice_company("Test Agro SRL", f"ro {VALID_CUI}", self.office)
        self.assertRecordValues(
            company,
            [
                {
                    "name": "Test Agro SRL",
                    "is_company": True,
                    "vat": f"RO{VALID_CUI}",
                    "state_id": self.county.id,
                    "city": "Craiova",
                    "street": "Str. Sediu 2",
                    "zip": "200001",
                    "country_id": self.env.ref("base.ro").id,
                    "email": "ion@example.com",
                }
            ],
        )
        # The customer keeps its own (delivery) address, not the registered office.
        self.assertRecordValues(
            self.customer,
            [{"parent_id": company.id, "type": "delivery", "street": "Str. Livrare 1", "city": "Bacau"}],
        )
        self.assertEqual(self.order.partner_id, self.customer)

    def test_existing_company_gets_a_new_invoice_address_with_the_typed_data(self):
        existing = self.Partner.create(
            {"name": "Existing SRL", "is_company": True, "vat": VALID_CUI, "street": "Secret 1", "city": "Cluj"}
        )
        invoice_address = self.order._tb_prepare_invoice_company("Typed name", f"RO{VALID_CUI}", self.office)
        # The order shows only what the visitor typed, the company recorded is left as it is.
        self.assertRecordValues(
            invoice_address,
            [
                {
                    "name": "Typed name",
                    "type": "invoice",
                    "parent_id": existing.id,
                    "street": "Str. Sediu 2",
                    "city": "Craiova",
                    "is_company": False,
                }
            ],
        )
        self.assertEqual(invoice_address.commercial_partner_id, existing)
        # The same name and registered office typed again reuse the invoice address.
        again = self.order._tb_prepare_invoice_company("Typed name", VALID_CUI, self.office)
        self.assertEqual(again, invoice_address)
        other_office = dict(self.office, street="Str. Alta 3")
        other = self.order._tb_prepare_invoice_company("Typed name", VALID_CUI, other_office)
        self.assertNotEqual(other, invoice_address)
        self.assertEqual(other.parent_id, existing)
        self.assertRecordValues(existing, [{"name": "Existing SRL", "street": "Secret 1", "city": "Cluj"}])
        # The customer is not attached to the company.
        self.assertFalse(self.customer.parent_id)
        self.assertEqual(self.customer.commercial_partner_id, self.customer)

    def test_company_typed_again_is_reused(self):
        company = self.order._tb_prepare_invoice_company("Test Agro SRL", VALID_CUI, self.office)
        again = self.order._tb_prepare_invoice_company("Test Agro SRL", f"RO{VALID_CUI}", self.office)
        self.assertEqual(again, company)
        self.assertFalse(company.child_ids.filtered(lambda child: child.type == "invoice"))

    def test_company_of_another_company_is_not_used(self):
        other_company = self.env["res.company"].create({"name": "Other Co"})
        self.Partner.create(
            {"name": "Foreign SRL", "is_company": True, "vat": VALID_CUI, "company_id": other_company.id}
        )
        company = self.order._tb_prepare_invoice_company("Test Agro SRL", VALID_CUI, self.office)
        self.assertTrue(company.is_company)
        self.assertEqual(company.name, "Test Agro SRL")
        self.assertFalse(company.company_id)


@tagged("post_install", "-at_install")
class TestCheckoutCompanyController(WebsiteSaleCommon):
    """The address form of the checkout, through the controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.partner"].search([("vat", "in", [VALID_CUI, f"RO{VALID_CUI}"])]).action_archive()
        cls.romania = cls.env.ref("base.ro")
        cls.county = cls.env["res.country.state"].search([("country_id", "=", cls.romania.id)], limit=1)

    def setUp(self):
        super().setUp()
        self.controller = TbWebsiteSale()
        # The customer of the cart is the current user, who fills in their main address.
        self.customer = self.env.user.partner_id
        self.customer.write({"parent_id": False, "is_company": False})
        self.order = self._create_so(partner_id=self.customer.id)
        self.form = {
            "partner_id": str(self.customer.id),
            "address_type": "delivery",
            "use_delivery_as_billing": "true",
            "tb_lastname": "Popescu",
            "tb_firstname": "Ion Vasile",
            "name": "",
            "email": "ion@example.com",
            "phone": "+40740123456",
            "street": "Str. Livrare 1",
            "city": "Bacau",
            "zip": "600001",
            "country_id": str(self.romania.id),
            "state_id": str(self.county.id),
            "tb_company": "true",
            "tb_company_name": "Test Agro SRL",
            "tb_company_vat": VALID_CUI,
            "tb_company_state_id": str(self.county.id),
            "tb_company_city": "Craiova",
            "tb_company_street": "Str. Sediu 2",
            "tb_company_zip": "200001",
        }

    def _submit(self, **changes):
        with MockRequest(self.env, website=self.website, sale_order_id=self.order.id) as request:
            request.httprequest.method = "POST"
            result = self.controller.shop_address_submit(**dict(self.form, **changes))
        result = result.get_data(as_text=True) if hasattr(result, "get_data") else result
        return json.loads(result)

    def _companies(self):
        return self.env["res.partner"].search([("vat", "in", [VALID_CUI, f"RO{VALID_CUI}"]), ("is_company", "=", True)])

    def test_name_is_last_name_then_first_name(self):
        feedback = self._submit(tb_company="false")
        self.assertNotIn("invalid_fields", feedback, feedback)
        customer = self.order.partner_id
        self.assertEqual(customer.name, "Popescu Ion Vasile")
        self.assertEqual(self.order.partner_invoice_id, customer)

    def test_invalid_vat_is_rejected_and_no_company_is_created(self):
        feedback = self._submit(tb_company_vat="18547291")
        self.assertIn("tb_company_vat", feedback["invalid_fields"])
        self.assertFalse(self._companies())
        self.assertFalse(self.customer.parent_id)

    def test_company_billing_only_for_deliveries_in_romania(self):
        # Delivered abroad, the domestic VAT of a Romanian company would not apply.
        hungary = self.env.ref("base.hu")
        feedback = self._submit(country_id=str(hungary.id), state_id="", zip="1011")
        self.assertIn("tb_company", feedback["invalid_fields"])
        self.assertFalse(self._companies())

    def test_registered_office_is_required_even_for_a_recorded_company(self):
        # The form asks the same whether or not the CUI belongs to a customer.
        self.env["res.partner"].create({"name": "Existing SRL", "is_company": True, "vat": VALID_CUI})
        feedback = self._submit(tb_company_street="", tb_company_zip="")
        self.assertTrue({"tb_company_street", "tb_company_zip"} <= set(feedback["invalid_fields"]))
        self.assertNotEqual(self.order.partner_invoice_id.parent_id.vat, VALID_CUI)

    def test_new_company_is_invoiced(self):
        feedback = self._submit()
        self.assertNotIn("invalid_fields", feedback)
        company = self._companies()
        self.assertEqual(len(company), 1)
        self.assertEqual(self.order.partner_invoice_id, company)
        self.assertEqual(self.order.partner_id.parent_id, company)
        self.assertEqual(self.order.partner_shipping_id.street, "Str. Livrare 1")

    def test_recorded_company_is_invoiced_without_showing_its_data(self):
        existing = self.env["res.partner"].create(
            {"name": "Existing SRL", "is_company": True, "vat": VALID_CUI, "street": "Secret 1"}
        )
        self._submit(tb_company_name="Typed name")
        invoice_address = self.order.partner_invoice_id
        self.assertEqual(invoice_address.commercial_partner_id, existing)
        self.assertEqual((invoice_address.name, invoice_address.street), ("Typed name", "Str. Sediu 2"))
        # The checkout offers it as the billing address, next to the customer's own.
        with MockRequest(self.env, website=self.website, sale_order_id=self.order.id):
            values = self.controller._prepare_checkout_page_values(self.order)
        self.assertIn(invoice_address, values["billing_addresses"])
        self.assertFalse(self.order.partner_id.parent_id)

    def test_registered_office_county_must_be_of_romania(self):
        other_state = self.env["res.country.state"].search([("country_id.code", "!=", "RO")], limit=1)
        self.romania.sudo().state_required = True
        feedback = self._submit(tb_company_state_id=str(other_state.id))
        # Dropped, the county is then missing: it is required in Romania.
        self.assertIn("tb_company_state_id", feedback["invalid_fields"])
        self.assertFalse(self._companies())
        self.romania.sudo().state_required = False
        self._submit(tb_company_state_id=str(other_state.id))
        self.assertFalse(self._companies().state_id)
