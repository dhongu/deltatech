# tests/test_stock_picking.py

from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
    def setUp(self):
        super().setUp()

        # Define the company
        self.company = self.env.ref("base.main_company")

        # Set up the data needed for the test
        self.stock_picking = self.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_stock").id,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                "company_id": self.company.id,
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "company_id": self.company.id,
            }
        )

        self.packaging = self.env["product.packaging"].create(
            {
                "name": "Test Packaging",
                "product_id": self.product.id,
                "qty": 5,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "package_type_id": self.env["stock.package.type"].create({"name": "Test Package Type"}).id,
                "company_id": self.company.id,
            }
        )

        self.move = self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 10,
                "product_uom": self.env.ref("uom.product_uom_unit").id,
                "picking_id": self.stock_picking.id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "product_packaging_id": self.packaging.id,
                "company_id": self.company.id,
            }
        )

    def test_pre_put_in_pack_hook_no_packaging(self):
        # Create a move line without packaging
        move_line = self.env["stock.move.line"].create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "quantity": 10,
                "company_id": self.company.id,
            }
        )

        # Run the method to be tested
        self.stock_picking._pre_put_in_pack_hook(move_line)

    def test_pre_put_in_pack_hook_with_packaging(self):
        # Create a move line with packaging
        move_line = self.env["stock.move.line"].create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "quantity": 10,
                "company_id": self.company.id,
            }
        )

        # Run the method to be tested
        self.stock_picking._pre_put_in_pack_hook(move_line)

    def test_pre_put_in_pack_hook_with_remainder(self):
        # Create a move line with packaging and a remainder
        move_line = self.env["stock.move.line"].create(
            {
                "move_id": self.move.id,
                "product_id": self.product.id,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "location_id": self.stock_picking.location_id.id,
                "location_dest_id": self.stock_picking.location_dest_id.id,
                "quantity": 12,  # 2 units more than a multiple of the packaging qty (5)
                "company_id": self.company.id,
            }
        )

        # Run the method to be tested
        self.stock_picking._pre_put_in_pack_hook(move_line)
