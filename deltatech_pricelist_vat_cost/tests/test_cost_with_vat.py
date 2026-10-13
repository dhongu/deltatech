from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCostWithVat(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_tax = cls.env["account.tax"].create(
            {"name": "Test purchase 21%", "type_tax_use": "purchase", "amount_type": "percent", "amount": 21}
        )
        cls.sale_tax = cls.env["account.tax"].create(
            {"name": "Test sale 21%", "type_tax_use": "sale", "amount_type": "percent", "amount": 21}
        )

    def _create_product(self, supplier_taxes, sale_taxes):
        return self.env["product.product"].create(
            {
                "name": "Test cost with VAT",
                "standard_price": 100,
                "supplier_taxes_id": [(6, 0, supplier_taxes.ids)],
                "taxes_id": [(6, 0, sale_taxes.ids)],
            }
        )

    def _assert_cost_with_vat(self, product, expected):
        self.assertAlmostEqual(product.standard_price_with_vat, expected)
        self.assertAlmostEqual(product.product_tmpl_id.standard_price_with_vat, expected)

    def test_purchase_taxes_only(self):
        product = self._create_product(self.purchase_tax, self.env["account.tax"])
        self._assert_cost_with_vat(product, 121)

    def test_sale_taxes_only(self):
        product = self._create_product(self.env["account.tax"], self.sale_tax)
        self._assert_cost_with_vat(product, 100)

    def test_both_taxes(self):
        product = self._create_product(self.purchase_tax, self.sale_tax)
        self._assert_cost_with_vat(product, 121)

    def test_no_taxes(self):
        product = self._create_product(self.env["account.tax"], self.env["account.tax"])
        self._assert_cost_with_vat(product, 100)

    def test_changing_purchase_taxes_invalidates(self):
        product = self._create_product(self.env["account.tax"], self.sale_tax)
        self._assert_cost_with_vat(product, 100)
        product.supplier_taxes_id = self.purchase_tax
        self._assert_cost_with_vat(product, 121)
        product.supplier_taxes_id = False
        self._assert_cost_with_vat(product, 100)

    def test_changing_purchase_tax_amount_invalidates(self):
        product = self._create_product(self.purchase_tax, self.env["account.tax"])
        self._assert_cost_with_vat(product, 121)
        self.purchase_tax.amount = 11
        self._assert_cost_with_vat(product, 111)

    def test_multi_company_uses_current_company_taxes(self):
        country = self.env.ref("base.ro")
        company_b = self.env["res.company"].create({"name": "Test company B", "country_id": country.id})
        tax_group_b = self.env["account.tax.group"].create(
            {"name": "Test tax group B", "company_id": company_b.id, "country_id": country.id}
        )
        purchase_tax_b = self.env["account.tax"].create(
            {
                "name": "Test purchase B 11%",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 11,
                "company_id": company_b.id,
                "tax_group_id": tax_group_b.id,
            }
        )
        # shared product carrying the default purchase tax of both companies
        product = self._create_product(self.purchase_tax | purchase_tax_b, self.env["account.tax"])
        product.with_company(company_b).standard_price = 200
        # read alternately in the same transaction: the value must follow the company
        self._assert_cost_with_vat(product, 121)
        self._assert_cost_with_vat(product.with_company(company_b), 222)
        self._assert_cost_with_vat(product, 121)

    def test_pricelist_based_on_cost_with_vat(self):
        product = self._create_product(self.purchase_tax, self.env["account.tax"])
        pricelist = self.env["product.pricelist"].create(
            {
                "name": "Test cost with VAT",
                "currency_id": product.currency_id.id,
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "standard_price_with_vat",
                            "price_surcharge": 10,
                        },
                    )
                ],
            }
        )
        self.assertAlmostEqual(pricelist._get_product_price(product, 1.0), 131)
        self.assertAlmostEqual(pricelist._get_product_price(product.product_tmpl_id, 1.0), 131)
