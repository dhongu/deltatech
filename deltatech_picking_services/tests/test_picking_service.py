# ©  2008-now Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestPickingServiceLine(TransactionCase):
    def setUp(self):
        super().setUp()

        # Define the company
        self.company = self.env.ref("base.main_company")

        # Create a stock picking type
        self.picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Test Picking Type",
                "code": "internal",
                "sequence_code": "INT",
                "company_id": self.company.id,
            }
        )

        # Create a stock picking
        self.stock_picking = self.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_stock").id,
                "picking_type_id": self.picking_type.id,
                "company_id": self.company.id,
            }
        )

        # Create a service product
        self.service_product = self.env["product.product"].create(
            {
                "name": "Test Service",
                "type": "service",
                "uom_id": self.env.ref("uom.product_uom_hour").id,
                "uom_po_id": self.env.ref("uom.product_uom_hour").id,
                "company_id": self.company.id,
            }
        )

    def test_create_picking_service_line(self):
        # Create a picking service line
        picking_service_line = self.env["picking.service.line"].create(
            {
                "product_id": self.service_product.id,
                "product_uom": self.service_product.uom_id.id,
                "product_uom_qty": 2,
                "price_unit": 50,
                "picking_id": self.stock_picking.id,
            }
        )

        # Check that the picking service line is created correctly
        self.assertEqual(picking_service_line.product_id, self.service_product)
        self.assertEqual(picking_service_line.product_uom, self.service_product.uom_id)
        self.assertEqual(picking_service_line.product_uom_qty, 2)
        self.assertEqual(picking_service_line.price_unit, 50)
        self.assertEqual(picking_service_line.price_subtotal, 100)

    def test_onchange_product_id(self):
        # Create a picking service line
        picking_service_line = self.env["picking.service.line"].new(
            {
                "product_id": self.service_product.id,
            }
        )
        picking_service_line._onchange_product_id()

        # Check that the onchange method sets the appropriate fields
        self.assertEqual(picking_service_line.product_uom, self.service_product.uom_id)
        self.assertEqual(picking_service_line.description_picking, self.service_product.name)
