# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleCatalogWebsite(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        PublicCateg = cls.env["product.public.category"]
        cls.categ_parent = PublicCateg.create({"name": "TST Parent"})
        cls.categ_child = PublicCateg.create({"name": "TST Child", "parent_id": cls.categ_parent.id})
        cls.categ_other = PublicCateg.create({"name": "TST Other"})
        cls.categ_unused = PublicCateg.create({"name": "TST Unused"})
        cls.internal_categ = cls.env["product.category"].create({"name": "TST Internal"})
        cls.product_child = cls.env["product.product"].create(
            {
                "name": "TST Product Child",
                "type": "consu",
                "categ_id": cls.internal_categ.id,
                "public_categ_ids": [(6, 0, cls.categ_child.ids)],
            }
        )
        cls.product_child2 = cls.env["product.product"].create(
            {
                "name": "TST Product Child 2",
                "type": "consu",
                "public_categ_ids": [(6, 0, (cls.categ_child | cls.categ_other).ids)],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "TST Customer"})
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.test_domain = [("id", "in", (cls.product_child | cls.product_child2).ids)]

    def _values_by_id(self, result):
        return {val["id"]: val for val in result["values"]}

    def test_action_add_from_catalog_swaps_views(self):
        action = self.order.action_add_from_catalog()
        kanban = self.env.ref("deltatech_sale_catalog_website.product_view_kanban_catalog_website")
        search = self.env.ref("deltatech_sale_catalog_website.product_view_search_catalog_website")
        self.assertEqual(action["views"], [(kanban.id, "kanban"), (False, "form")])
        self.assertEqual(action["search_view_id"], [search.id, "search"])
        self.assertEqual(action["res_model"], "product.product")

    def test_other_field_uses_standard_range(self):
        result = self.env["product.product"].search_panel_select_range("categ_id", search_domain=self.test_domain)
        self.assertEqual(result["parent_field"], "parent_id")
        self.assertIn(self.internal_categ.id, self._values_by_id(result))

    def test_public_categ_not_expand_with_counters(self):
        result = self.env["product.product"].search_panel_select_range(
            "public_categ_ids",
            search_domain=self.test_domain,
            enable_counters=True,
            expand=False,
        )
        self.assertEqual(result["parent_field"], "parent_id")
        values = self._values_by_id(result)
        # only used categories and their parents are listed
        self.assertIn(self.categ_parent.id, values)
        self.assertIn(self.categ_child.id, values)
        self.assertIn(self.categ_other.id, values)
        self.assertNotIn(self.categ_unused.id, values)
        # short name instead of the full path
        self.assertEqual(values[self.categ_child.id]["display_name"], "TST Child")
        self.assertEqual(values[self.categ_child.id]["parent_id"], self.categ_parent.id)
        self.assertFalse(values[self.categ_parent.id]["parent_id"])
        # counters, with the global (cascading) count on the parent
        self.assertEqual(values[self.categ_child.id]["__count"], 2)
        self.assertEqual(values[self.categ_other.id]["__count"], 1)
        self.assertEqual(values[self.categ_parent.id]["__count"], 2)

    def test_public_categ_not_expand_without_counters(self):
        result = self.env["product.product"].search_panel_select_range(
            "public_categ_ids",
            search_domain=self.test_domain,
        )
        values = self._values_by_id(result)
        self.assertIn(self.categ_child.id, values)
        self.assertIn(self.categ_parent.id, values)
        self.assertNotIn(self.categ_unused.id, values)
        self.assertNotIn("__count", values[self.categ_child.id])

    def test_public_categ_expand_with_counters(self):
        result = self.env["product.product"].search_panel_select_range(
            "public_categ_ids",
            search_domain=self.test_domain,
            enable_counters=True,
            expand=True,
            comodel_domain=[("name", "=like", "TST %")],
        )
        values = self._values_by_id(result)
        # with expand all the categories are shown, even without products
        self.assertIn(self.categ_unused.id, values)
        self.assertEqual(values[self.categ_unused.id]["__count"], 0)
        self.assertEqual(values[self.categ_child.id]["__count"], 2)

    def test_public_categ_expand_without_counters_and_limit(self):
        result = self.env["product.product"].search_panel_select_range(
            "public_categ_ids",
            expand=True,
            comodel_domain=[("id", "in", (self.categ_unused | self.categ_other).ids)],
            limit=1,
            category_domain=[],
            filter_domain=[],
        )
        self.assertEqual(len(result["values"]), 1)
        self.assertNotIn("__count", result["values"][0])
