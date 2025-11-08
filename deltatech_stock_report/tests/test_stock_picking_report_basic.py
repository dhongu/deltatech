# © 2025 Deltatech / Terrabit
# Basic tests for deltatech_stock_report
# Purpose: ensure the SQL view model `stock.picking.report` is available and queryable.

from odoo.tests.common import TransactionCase


class TestStockPickingReportBasics(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Report = cls.env["stock.picking.report"]

    def test_model_is_available(self):
        # Model should be registered
        self.assertTrue(self.Report._name == "stock.picking.report")

    def test_fields_exist(self):
        # Sanity check for a few important fields that the view exposes
        for field in (
            "partner_id",
            "picking_type_id",
            "picking_id",
            "date",
            "company_id",
            "categ_id",
            "product_id",
            "product_uom",
            "location_id",
            "location_dest_id",
            "product_qty",
            "price",
            "amount",
            "commercial_partner_id",
            "product_weight",
        ):
            self.assertIn(field, self.Report._fields, msg=f"Missing field on report: {field}")

    def test_view_is_queryable(self):
        # The SQL view should exist and be queryable even if empty
        # search_count should not crash
        count = self.Report.search_count([])
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)
