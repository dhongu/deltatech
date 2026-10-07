from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteWarehouseCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "TEST Web WH Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "TEST Web WH Company B"})
        cls.website_a = cls.env["website"].create({"name": "TEST Website A", "company_id": cls.company_a.id})
        cls.warehouse_a = cls.env["stock.warehouse"].search([("company_id", "=", cls.company_a.id)], limit=1)
        cls.warehouse_b = cls.env["stock.warehouse"].search([("company_id", "=", cls.company_b.id)], limit=1)
        cls.warehouse_a.name = "TEST WH A"
        cls.warehouse_b.name = "TEST WH B"
        cls.product = cls.env["product.product"].create(
            {"name": "TEST shared product", "is_storable": True, "company_id": False}
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.warehouse_a.lot_stock_id, 3)
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.warehouse_b.lot_stock_id, 50)

    def _distribution(self):
        return (
            self.product.product_tmpl_id.with_context(website_id=self.website_a.id)
            .sudo()
            .get_warehouse_stock_distribution()
        )

    def test_foreign_company_warehouse_not_displayed(self):
        names = [line["warehouse"] for line in self._distribution()]
        self.assertIn(self.warehouse_a.name, names)
        self.assertNotIn(self.warehouse_b.name, names)

    def test_quantity_only_from_website_company(self):
        lines = {line["warehouse"]: line for line in self._distribution()}
        self.assertEqual(lines[self.warehouse_a.name]["quantity"], 3)
        self.assertEqual(lines[self.warehouse_a.name]["badge"], "grey")
