# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged

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

    def test_clean_and_validate_vat(self):
        self.assertEqual(self.Partner._tb_clean_company_vat(" ro 18.547.290 "), "RO18547290")
        self.assertTrue(self.Partner._tb_is_valid_company_vat(VALID_CUI))
        self.assertTrue(self.Partner._tb_is_valid_company_vat(f"RO{VALID_CUI}"))
        self.assertFalse(self.Partner._tb_is_valid_company_vat("18547291"))
        self.assertFalse(self.Partner._tb_is_valid_company_vat(""))

    def test_new_company_is_created_and_customer_becomes_its_contact(self):
        office = {"state_id": self.county.id, "city": "Craiova", "street": "Str. Sediu 2", "zip": "200001"}
        company = self.order._tb_set_invoice_company("Test Agro SRL", f"ro {VALID_CUI}", office)
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
        self.assertEqual(self.order.partner_invoice_id, company)
        self.assertEqual(self.order.partner_id, self.customer)

    def test_existing_company_is_invoiced_without_attaching_the_customer(self):
        existing = self.Partner.create({"name": "Existing SRL", "vat": VALID_CUI})
        company = self.order._tb_set_invoice_company("Other name", f"RO{VALID_CUI}")
        self.assertEqual(company, existing)
        self.assertEqual(self.order.partner_invoice_id, existing)
        self.assertFalse(self.customer.parent_id)
        self.assertEqual(existing.name, "Existing SRL")
        self.assertEqual(self.Partner.search_count([("vat", "in", [VALID_CUI, f"RO{VALID_CUI}"])]), 1)

    def test_company_of_another_company_is_not_used(self):
        other_company = self.env["res.company"].create({"name": "Other Co"})
        self.Partner.create({"name": "Foreign SRL", "vat": VALID_CUI, "company_id": other_company.id})
        company = self.order._tb_set_invoice_company("Test Agro SRL", VALID_CUI)
        self.assertEqual(company.name, "Test Agro SRL")
        self.assertFalse(company.company_id)
