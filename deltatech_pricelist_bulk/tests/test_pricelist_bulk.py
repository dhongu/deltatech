# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPricelistBulk(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create({"name": "TEST Bulk"})
        cls.categ = cls.env["product.category"].create({"name": "TEST Bulk Categ"})
        cls.child_categ = cls.env["product.category"].create({"name": "TEST Child", "parent_id": cls.categ.id})
        cls.templates = cls.env["product.template"].create(
            [
                {"name": "TEST A", "list_price": 100.0, "standard_price": 50.0, "categ_id": cls.categ.id},
                {"name": "TEST B", "list_price": 200.0, "standard_price": 80.0, "categ_id": cls.categ.id},
                {"name": "TEST C", "list_price": 300.0, "standard_price": 90.0, "categ_id": cls.child_categ.id},
            ]
        )

    def _add_wizard(self, **vals):
        return self.env["pricelist.bulk.add"].create(
            {"pricelist_id": self.pricelist.id, "product_tmpl_ids": [(6, 0, self.templates.ids)], **vals}
        )

    def _price(self, template, quantity=1.0):
        return self.pricelist._get_product_price(template.product_variant_id, quantity)

    def test_add_rules_fixed_price(self):
        self._add_wizard(compute_price="fixed", fixed_price=42.0).action_apply()
        items = self.pricelist.item_ids
        self.assertEqual(len(items), 3)
        self.assertEqual(set(items.mapped("applied_on")), {"1_product"})
        self.assertEqual(items.product_tmpl_id, self.templates)
        for template in self.templates:
            self.assertEqual(self._price(template), 42.0)

    def test_add_rules_formula(self):
        self._add_wizard(compute_price="formula", base="list_price", price_discount=10.0).action_apply()
        self.assertEqual(self._price(self.templates[0]), 90.0)
        self.assertEqual(self._price(self.templates[1]), 180.0)

    def test_add_rules_markup_on_cost(self):
        self._add_wizard(compute_price="formula", base="standard_price", price_markup=20.0).action_apply()
        self.assertEqual(self.pricelist.item_ids.mapped("price_discount"), [-20.0] * 3)
        self.assertEqual(self._price(self.templates[0]), 60.0)

    def test_existing_rule_policies(self):
        self._add_wizard(compute_price="fixed", fixed_price=10.0).action_apply()
        self._add_wizard(compute_price="fixed", fixed_price=20.0, existing_policy="skip").action_apply()
        self.assertEqual(len(self.pricelist.item_ids), 3)
        self.assertEqual(self._price(self.templates[0]), 10.0)

        self._add_wizard(compute_price="fixed", fixed_price=20.0, existing_policy="update").action_apply()
        self.assertEqual(len(self.pricelist.item_ids), 3)
        self.assertEqual(self._price(self.templates[0]), 20.0)

        self._add_wizard(compute_price="fixed", fixed_price=30.0, existing_policy="create").action_apply()
        self.assertEqual(len(self.pricelist.item_ids), 6)

    def test_other_min_quantity_is_new_rule(self):
        self._add_wizard(compute_price="fixed", fixed_price=10.0).action_apply()
        self._add_wizard(
            compute_price="fixed", fixed_price=8.0, min_quantity=10.0, existing_policy="update"
        ).action_apply()
        self.assertEqual(len(self.pricelist.item_ids), 6)
        self.assertEqual(self._price(self.templates[0], 1.0), 10.0)
        self.assertEqual(self._price(self.templates[0], 10.0), 8.0)

    def test_add_variant_and_category_rules(self):
        variants = self.templates.product_variant_id
        self.env["pricelist.bulk.add"].create(
            {
                "pricelist_id": self.pricelist.id,
                "applied_on": "0_product_variant",
                "product_ids": [(6, 0, variants.ids)],
                "fixed_price": 5.0,
            }
        ).action_apply()
        self.env["pricelist.bulk.add"].create(
            {
                "pricelist_id": self.pricelist.id,
                "applied_on": "2_product_category",
                "categ_ids": [(6, 0, self.categ.ids)],
                "compute_price": "percentage",
                "percent_price": 5.0,
            }
        ).action_apply()
        items = self.pricelist.item_ids
        self.assertEqual(items.filtered(lambda i: i.applied_on == "0_product_variant").product_id, variants)
        self.assertEqual(items.filtered(lambda i: i.applied_on == "2_product_category").categ_id, self.categ)

    def test_fill_products_from_categories(self):
        with Form(self.env["pricelist.bulk.add"].with_context(default_pricelist_id=self.pricelist.id)) as wizard:
            wizard.fill_categ_ids.add(self.categ)
            self.assertEqual(len(wizard.product_tmpl_ids), 3, "Subcategory products are added too")
            self.assertFalse(wizard.fill_categ_ids)

    def test_default_from_selected_products(self):
        wizard = (
            self.env["pricelist.bulk.add"]
            .with_context(active_model="product.template", active_ids=self.templates[:2].ids)
            .create({"pricelist_id": self.pricelist.id})
        )
        self.assertEqual(wizard.product_tmpl_ids, self.templates[:2])

    def test_add_without_products(self):
        wizard = self.env["pricelist.bulk.add"].create({"pricelist_id": self.pricelist.id})
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_apply_formula_on_rules(self):
        self._add_wizard(compute_price="fixed", fixed_price=10.0, min_quantity=1.0).action_apply()
        items = self.pricelist.item_ids
        action = self.pricelist.action_pricelist_bulk_formula()
        wizard = (
            self.env["pricelist.bulk.formula"]
            .with_context(**action["context"])
            .create({"compute_price": "formula", "base": "list_price", "price_discount": 25.0, "price_round": 1.0})
        )
        self.assertEqual(wizard.item_ids, items)
        wizard.action_apply()
        self.assertEqual(set(items.mapped("compute_price")), {"formula"})
        self.assertEqual(items.mapped("fixed_price"), [0.0] * 3, "Fixed price of the old type is cleared")
        self.assertEqual(items.mapped("min_quantity"), [1.0] * 3, "Min. quantity is kept when not changed")
        self.assertEqual(self._price(self.templates[1]), 150.0)

    def test_apply_only_quantity_and_dates(self):
        self._add_wizard(compute_price="fixed", fixed_price=10.0).action_apply()
        items = self.pricelist.item_ids
        wizard = (
            self.env["pricelist.bulk.formula"]
            .with_context(active_model="product.pricelist.item", active_ids=items[:2].ids)
            .create(
                {
                    "change_price": False,
                    "change_min_quantity": True,
                    "min_quantity": 5.0,
                    "change_dates": True,
                    "date_start": "2026-01-01 00:00:00",
                    "date_end": "2026-12-31 23:59:59",
                }
            )
        )
        wizard.action_apply()
        self.assertEqual(items[:2].mapped("min_quantity"), [5.0, 5.0])
        self.assertEqual(items[2].min_quantity, 0.0)
        self.assertEqual(items.mapped("fixed_price"), [10.0] * 3)
        self.assertTrue(all(items[:2].mapped("date_end")))

    def test_apply_nothing_to_change(self):
        self._add_wizard(fixed_price=10.0).action_apply()
        wizard = self.env["pricelist.bulk.formula"].create(
            {"item_ids": [(6, 0, self.pricelist.item_ids.ids)], "change_price": False}
        )
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_formula_on_own_pricelist(self):
        self._add_wizard(fixed_price=10.0).action_apply()
        wizard = self.env["pricelist.bulk.formula"].create(
            {
                "item_ids": [(6, 0, self.pricelist.item_ids.ids)],
                "compute_price": "formula",
                "base": "pricelist",
                "base_pricelist_id": self.pricelist.id,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_apply()
