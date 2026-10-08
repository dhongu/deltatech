# ©  2008-now Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import AccessError
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

    def test_service_line_company_isolation(self):
        """PICKSERVICE-001: a stock user cannot reach the service lines of another company"""
        other_company = self.env["res.company"].create({"name": "Picking Services Other Company"})
        other_warehouse = self.env["stock.warehouse"].search([("company_id", "=", other_company.id)], limit=1)
        other_picking = self.env["stock.picking"].create(
            {
                "location_id": other_warehouse.lot_stock_id.id,
                "location_dest_id": other_warehouse.lot_stock_id.id,
                "picking_type_id": other_warehouse.int_type_id.id,
                "company_id": other_company.id,
            }
        )
        other_line = self.env["picking.service.line"].create(
            {
                "product_id": self.service_product.id,
                "product_uom": self.service_product.uom_id.id,
                "price_unit": 75,
                "picking_id": other_picking.id,
            }
        )
        own_line = self.env["picking.service.line"].create(
            {
                "product_id": self.service_product.id,
                "product_uom": self.service_product.uom_id.id,
                "price_unit": 50,
                "picking_id": self.stock_picking.id,
            }
        )
        self.assertEqual(other_line.company_id, other_company)

        stock_user = self.env["res.users"].create(
            {
                "name": "Stock User Main Company",
                "login": "picking_services_stock_user",
                "company_id": self.company.id,
                "company_ids": [(6, 0, self.company.ids)],
                "group_ids": [(6, 0, self.env.ref("stock.group_stock_user").ids)],
            }
        )
        lines = self.env["picking.service.line"].with_user(stock_user)
        found = lines.search([("id", "in", (other_line | own_line).ids)])
        self.assertEqual(found, own_line.with_user(stock_user))
        with self.assertRaises(AccessError):
            other_line.with_user(stock_user).price_unit  # noqa: B018
        with self.assertRaises(AccessError):
            other_line.with_user(stock_user).write({"price_unit": 0.0})
        with self.assertRaises(AccessError):
            other_line.with_user(stock_user).unlink()

    def test_service_lines_deleted_with_picking(self):
        line = self.env["picking.service.line"].create(
            {
                "product_id": self.service_product.id,
                "product_uom": self.service_product.uom_id.id,
                "picking_id": self.stock_picking.id,
            }
        )
        self.stock_picking.unlink()
        self.assertFalse(line.exists())
