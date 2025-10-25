# © 2015-2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestComputeWarehouseStocks(TransactionCase):
    def setUp(self):
        super().setUp()
        # Use main demo warehouse that exists in base data
        self.company = self.env.user.company_id
        self.wh1 = self.env.ref("stock.warehouse0")
        self.loc1 = self.wh1.lot_stock_id

        # Create a storable product and put stock in WH1
        self.product = self.env["product.product"].create(
            {
                "name": "WH Stocks Prod",
                "is_storable": True,
                "standard_price": 1.0,
            }
        )
        self.template = self.product.product_tmpl_id
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.loc1.id,
                "quantity": 4.0,
            }
        )

    def test_compute_warehouse_stocks_single_and_multi(self):
        # With a single warehouse in company, field should be False
        self.template._compute_warehouse_stocks()
        self.assertFalse(self.template.warehouse_stock)

        # Create a second warehouse in the same company
        wh2 = self.env["stock.warehouse"].create(
            {
                "name": "Test WH2",
                "code": "T2",
                "company_id": self.company.id,
            }
        )
        # Seed stock in the second warehouse's stock location
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": wh2.lot_stock_id.id,
                "quantity": 6.0,
            }
        )

        # Recompute without and with display_free_quantity
        self.template._compute_warehouse_stocks()
        text = self.template.warehouse_stock or ""
        # Expect codes and quantities for both warehouses present
        self.assertIn(self.wh1.code, text)
        self.assertIn("4.0", text)
        self.assertIn("T2", text)
        self.assertIn("6.0", text)

        # With display_free_quantity=True and no outgoing moves, same values
        tmpl_ctx = self.template.with_context(display_free_quantity=True)
        tmpl_ctx._compute_warehouse_stocks()
        text2 = tmpl_ctx.warehouse_stock or ""
        self.assertIn(self.wh1.code, text2)
        self.assertIn("4.0", text2)
        self.assertIn("T2", text2)
        self.assertIn("6.0", text2)
