# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPriceCateg(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.template"].create(
            {
                "name": "test",
                "list_price": 200,
                "standard_price": 50,
                "last_purchase_price": 60,
            }
        )

    def test_price_categ_by_last_purchase_price(self):
        product = Form(self.product)
        product.list_price_base = "last_purchase_price"
        product.percent_bronze = 0.80
        product.percent_copper = 0.70
        product.percent_silver = 0.60
        product.percent_gold = 0.50
        product.save()

    def test_price_categ_by_standard_price(self):
        product = Form(self.product)
        product.list_price_base = "standard_price"
        product.percent_bronze = 0.80
        product.percent_copper = 0.70
        product.percent_silver = 0.60
        product.percent_gold = 0.50
        product.save()

    def test_price_categ_by_list_price(self):
        product = Form(self.product)
        product.list_price_base = "list_price"
        product.percent_bronze = -0.25
        product.percent_copper = -0.30
        product.percent_silver = -0.35
        product.percent_gold = -0.40
        product.save()


class TestPriceCategTaxes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        tax_model = cls.env["account.tax"]
        tax_group = cls.env["account.tax.group"].create({"name": "Test price categ"})
        cls.tax_fixed_inc = tax_model.create(
            {
                "name": "Test fixed included 10",
                "amount_type": "fixed",
                "amount": 10,
                "type_tax_use": "sale",
                "tax_group_id": tax_group.id,
                "price_include_override": "tax_included",
            }
        )
        cls.tax_percent_inc = tax_model.create(
            {
                "name": "Test 21% included",
                "amount_type": "percent",
                "amount": 21,
                "type_tax_use": "sale",
                "tax_group_id": tax_group.id,
                "price_include_override": "tax_included",
            }
        )
        cls.tax_percent_exc = tax_model.create(
            {
                "name": "Test 5% excluded",
                "amount_type": "percent",
                "amount": 5,
                "type_tax_use": "sale",
                "tax_group_id": tax_group.id,
                "price_include_override": "tax_excluded",
            }
        )

    def _create_product(self, base, taxes, **vals):
        values = {
            "name": "test taxes",
            "list_price": 220,
            "standard_price": 200,
            "last_purchase_price": 200,
            "list_price_base": base,
            "taxes_id": [(6, 0, taxes.ids)],
        }
        values.update(vals)
        return self.env["product.template"].create(values)

    def test_fixed_included_tax_on_cost(self):
        # PRICE-001: a fixed included tax of 10 on a cost of 200 gives 210, not 220
        for base in ("standard_price", "last_purchase_price"):
            product = self._create_product(base, self.tax_fixed_inc)
            self.assertAlmostEqual(product.list_price_bronze, 210.0)
            self.assertAlmostEqual(product.list_price_gold, 210.0)

    def test_fixed_included_tax_on_list_price(self):
        # PRICE-001: the fixed tax removed by compute_all must not be added back as a percentage
        product = self._create_product("list_price", self.tax_fixed_inc, percent_bronze=0.1)
        self.assertAlmostEqual(product.list_price_gold, 220.0)
        self.assertAlmostEqual(product.list_price_bronze, 242.0)

    def test_percent_included_tax_on_cost(self):
        product = self._create_product("standard_price", self.tax_percent_inc)
        self.assertAlmostEqual(product.list_price_gold, 242.0)

    def test_excluded_tax_is_not_added(self):
        # PRICE-001: taxes not included in price are not added to the category prices
        product = self._create_product("standard_price", self.tax_percent_inc | self.tax_percent_exc)
        self.assertAlmostEqual(product.list_price_gold, 242.0)
        product = self._create_product("list_price", self.tax_percent_inc | self.tax_percent_exc, list_price=121)
        self.assertAlmostEqual(product.list_price_gold, 121.0)

    def test_zero_cost_stays_zero(self):
        # a product without cost keeps 0 on all tiers, even with a fixed included tax
        product = self._create_product(
            "last_purchase_price", self.tax_fixed_inc, standard_price=0, last_purchase_price=0
        )
        self.assertEqual(product.list_price_gold, 0.0)
        self.assertEqual(product.list_price_bronze, 0.0)

    def test_tax_change_recomputes_prices(self):
        # PRICE-002: changing an existing tax recomputes the stored category prices
        tax = self.tax_percent_inc.copy({"name": "Test 21% included (copy)"})
        product = self._create_product("standard_price", tax)
        self.assertAlmostEqual(product.list_price_gold, 242.0)
        tax.amount = 11
        self.assertAlmostEqual(product.list_price_gold, 222.0)
        tax.price_include_override = "tax_excluded"
        self.assertAlmostEqual(product.list_price_gold, 200.0)

    def test_group_of_included_taxes(self):
        # PRICE-001: the children of a group tax are computed by the tax engine
        group = self.env["account.tax"].create(
            {
                "name": "Test group",
                "amount_type": "group",
                "type_tax_use": "sale",
                "tax_group_id": self.tax_fixed_inc.tax_group_id.id,
                "children_tax_ids": [(6, 0, (self.tax_fixed_inc | self.tax_percent_inc).ids)],
            }
        )
        product = self._create_product("standard_price", group)
        self.assertAlmostEqual(product.list_price_gold, 252.0)
