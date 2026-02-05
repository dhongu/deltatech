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
