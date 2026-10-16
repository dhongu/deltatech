from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create necessary records for the test
        self.company = self.env["res.company"].create({"name": "Test Company"})

        self.partner_customer = self.env["res.partner"].create({"name": "Customer Partner"})
        self.partner_shipping = self.env["res.partner"].create({"name": "Shipping Partner"})
        self.warehouse_partner = self.env["res.partner"].create({"name": "Warehouse Partner"})

        self.warehouse = self.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse",
                "code": "TW",
                "company_id": self.company.id,
                "partner_id": self.warehouse_partner.id,
            }
        )

        self.picking_type_out = self.env["stock.picking.type"].create(
            {
                "name": "Outgoing",
                "code": "outgoing",
                "sequence_code": "OUT",
                "warehouse_id": self.warehouse.id,
                "company_id": self.company.id,
            }
        )

        self.picking_type_in = self.env["stock.picking.type"].create(
            {
                "name": "Incoming",
                "code": "incoming",
                "sequence_code": "IN",
                "warehouse_id": self.warehouse.id,
                "company_id": self.company.id,
            }
        )

        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_customer.id,
                "partner_shipping_id": self.partner_shipping.id,
                "company_id": self.company.id,
            }
        )
        self.sale_order = self.sale_order

    def test_outgoing_picking(self):
        # Create an outgoing stock picking
        outgoing_picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner_customer.id,
                "picking_type_id": self.picking_type_out.id,
            }
        )

        # Compute the delivery address
        outgoing_picking._compute_delivery_address_id()

        # Check that the shipping address is the partner of the picking
        self.assertEqual(outgoing_picking.partner_shipping_id, self.partner_customer)

    def test_incoming_picking_without_sale(self):
        # Create an incoming stock picking without a sale order
        incoming_picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner_customer.id,
                "picking_type_id": self.picking_type_in.id,
            }
        )

        # Compute the delivery address
        incoming_picking._compute_delivery_address_id()

        # Check that the shipping address is the partner of the warehouse
        self.assertEqual(incoming_picking.partner_shipping_id, self.warehouse_partner)

    def test_incoming_picking_with_sale(self):
        # Create an incoming stock picking with a sale order
        incoming_picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner_customer.id,
                "picking_type_id": self.picking_type_in.id,
                "sale_id": self.sale_order.id,
            }
        )
        incoming_picking.sale_id = self.sale_order.id

        # Compute the delivery address
        incoming_picking._compute_delivery_address_id()

        # Check that the shipping address is the partner_shipping_id from the sale order
        self.assertEqual(incoming_picking.partner_shipping_id, self.partner_shipping)
