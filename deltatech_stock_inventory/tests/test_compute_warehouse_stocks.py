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

    def _make_move(self, location, location_dest, qty):
        move = self.env["stock.move"].create(
            {
                "name": "WH Stocks Move",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": qty,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
            }
        )
        move._action_confirm()
        return move

    def test_compute_warehouse_stocks_detailed_transit(self):
        wh2 = self.env["stock.warehouse"].create(
            {
                "name": "Test WH2",
                "code": "T2",
                "company_id": self.company.id,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": wh2.lot_stock_id.id,
                "quantity": 6.0,
            }
        )
        self.wh1.kanban_display_stock = "detailed"

        # pending transfer from the other warehouse -> counted as transit
        self._make_move(wh2.lot_stock_id, self.loc1, 3.0)
        # receipt from supplier -> not counted
        supplier_location = self.env.ref("stock.stock_location_suppliers")
        self._make_move(supplier_location, self.loc1, 5.0)
        # move inside the same warehouse -> not counted
        shelf = self.env["stock.location"].create(
            {"name": "WH Stocks Shelf", "location_id": self.loc1.id, "usage": "internal"}
        )
        self._make_move(self.loc1, shelf, 2.0)

        self.template._compute_warehouse_stocks()
        text = self.template.warehouse_stock or ""
        self.assertIn(f"{self.wh1.code}: 4.0 (T: 3.0)", text)
        self.assertIn("T2: 6.0", text)
        # transit is informative only, free stock is unchanged
        self.assertIn("FREE STOCK: 4.0", text)

    def test_compute_warehouse_stocks_detailed_transit_location(self):
        self.env["stock.warehouse"].create(
            {
                "name": "Test WH2",
                "code": "T2",
                "company_id": self.company.id,
            }
        )
        self.wh1.kanban_display_stock = "detailed"
        transit_location = self.env["stock.location"].create(
            {
                "name": "WH Stocks Transit",
                "usage": "transit",
                "company_id": self.company.id,
            }
        )
        # second leg of a two step transfer, waiting in a transit location
        self._make_move(transit_location, self.loc1, 7.0)

        self.template._compute_warehouse_stocks()
        text = self.template.warehouse_stock or ""
        self.assertIn(f"{self.wh1.code}: 4.0 (T: 7.0)", text)
        self.assertIn("FREE STOCK: 4.0", text)
