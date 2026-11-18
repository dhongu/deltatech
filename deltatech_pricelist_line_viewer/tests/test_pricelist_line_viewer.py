from odoo.tests.common import TransactionCase


class TestPricelistLineViewer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create({"name": "Test Pricelist"})

    def test_action_view_lines(self):
        action = self.pricelist.action_view_lines()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "product.pricelist.item")
        self.assertEqual(action["context"]["default_pricelist_id"], self.pricelist.id)

        # Verificăm dacă view-ul specificat există (ar trebui să fie definit în XML)
        tree_view_id = self.env.ref("deltatech_pricelist_line_viewer.product_pricelist_lines_view").id
        self.assertIn((tree_view_id, "list"), action["views"])

    def test_action_search_view_and_title(self):
        """The search view goes as [id] (the web client reads action.search_view_id[0]), the title is translatable."""
        action = self.pricelist.action_view_lines()
        search_view = self.env.ref("product.product_pricelist_item_view_search")
        self.assertEqual(action["search_view_id"], [search_view.id])
        self.assertEqual(action["name"], "Pricelist Rules")

    def test_price_column_shows_the_rule(self):
        """The Price column is the rule label, so a discount rule does not show 0.00."""
        tree_view_id = self.env.ref("deltatech_pricelist_line_viewer.product_pricelist_lines_view").id
        arch = self.env["product.pricelist.item"].get_view(tree_view_id, "list")["arch"]
        self.assertIn('name="price"', arch)
        item = self.env["product.pricelist.item"].create(
            {"pricelist_id": self.pricelist.id, "compute_price": "percentage", "percent_price": 12.0}
        )
        self.assertFalse(item.fixed_price)
        self.assertIn("12", item.price)

    def test_access_rights_have_readable_names(self):
        for xmlid, name in (
            ("access_pricelist_editing", "Permit pricelist editing: Pricelist"),
            ("access_pricelist_item_editing", "Permit pricelist editing: Pricelist Rule"),
        ):
            self.assertEqual(self.env.ref(f"deltatech_pricelist_line_viewer.{xmlid}").name, name)
