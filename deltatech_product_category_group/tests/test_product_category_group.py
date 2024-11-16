from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a user group
        self.user_group = self.env["res.groups"].create(
            {
                "name": "Test Group",
            }
        )

        # Create a user associated with the user group
        self.user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "groups_id": [(6, 0, [self.user_group.id])],
            }
        )

        # Create a product category associated with the user group
        self.product_category = self.env["product.category"].create(
            {
                "name": "Test Category",
                "user_group_id": self.user_group.id,
            }
        )

        # Create a product associated with the product category
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "categ_id": self.product_category.id,
            }
        )

        # Create a stock picking with a move line that includes the product
        self.stock_picking = self.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_stock").id,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
            }
        )
        self.location_source = self.env["stock.location"].create(
            {
                "name": "Source Location",
                "usage": "internal",
            }
        )
        self.location_dest = self.env["stock.location"].create(
            {
                "name": "Destination Location",
                "usage": "internal",
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location_source.id,
                "quantity": 100.0,
            }
        )

        self.move = self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 10,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.stock_picking.id,
                "location_id": self.location_source.id,
                "location_dest_id": self.location_dest.id,
            }
        )

    def test_responsible_determination(self):
        # Call the responsible_determination method
        self.stock_picking.write({"user_id": False})
        self.stock_picking.action_assign()
        self.stock_picking.write({"user_id": False})
        self.stock_picking.responsible_determination()
