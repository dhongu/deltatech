from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestNegative(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_stock_multi_locations = cls.env.ref("stock.group_stock_multi_locations")
        cls.env.user.write({"groups_id": [(4, group_stock_multi_locations.id, 0)]})
        cls.env.company.no_negative_stock = True

        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.pack_location = cls.env.ref("stock.location_pack_zone")

        cls.product = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
            }
        )
        cls.product_lot = cls.env["product.product"].create(
            {
                "name": "Product B",
                "type": "product",
                "tracking": "lot",
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "ABC001",
                "product_id": cls.product_lot.id,
                "company_id": cls.env.company.id,
            }
        )

    def test_allow_positive(self):
        self.env["stock.quant"]._update_available_quantity(
            product_id=self.product, location_id=self.stock_location, quantity=10.0
        )
        move = self.env["stock.move"].create(
            {
                "name": "test_negative",
                "location_id": self.stock_location.id,
                "location_dest_id": self.pack_location.id,
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 10.0,
            }
        )
        move._action_confirm()
        move_line = self.env["stock.move.line"].create(move._prepare_move_line_vals())
        move_line.quantity = 10.0
        move._action_done()

    def test_prevent_negative(self):
        self.env["stock.quant"]._update_available_quantity(
            product_id=self.product, location_id=self.stock_location, quantity=5.0
        )
        move = self.env["stock.move"].create(
            {
                "name": "test_negative",
                "location_id": self.stock_location.id,
                "location_dest_id": self.pack_location.id,
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 10.0,
            }
        )
        move._action_confirm()
        move_line = self.env["stock.move.line"].create(move._prepare_move_line_vals())

        with self.assertRaises(UserError) as cm:
            move_line.quantity = 10.0
            move._action_done()
        self.assertRegex(cm.exception.args[0], "avoid negative stock")

    def test_allow_positive_lot(self):
        self.env["stock.quant"]._update_available_quantity(
            product_id=self.product_lot,
            location_id=self.stock_location,
            quantity=10.0,
            lot_id=self.lot,
        )
        move = self.env["stock.move"].create(
            {
                "name": "test_negative",
                "location_id": self.stock_location.id,
                "location_dest_id": self.pack_location.id,
                "product_id": self.product_lot.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 10.0,
            }
        )
        move._action_confirm()
        move_line = self.env["stock.move.line"].create(move._prepare_move_line_vals())
        move_line.lot_id = self.lot
        move_line.quantity = 10.0
        move._action_done()

    def test_prevent_negative_lot(self):
        self.env["stock.quant"]._update_available_quantity(
            product_id=self.product_lot,
            location_id=self.stock_location,
            quantity=5.0,
            lot_id=self.lot,
        )
        move = self.env["stock.move"].create(
            {
                "name": "test_negative",
                "location_id": self.stock_location.id,
                "location_dest_id": self.pack_location.id,
                "product_id": self.product_lot.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 10.0,
            }
        )
        move._action_confirm()
        move_line = self.env["stock.move.line"].create(move._prepare_move_line_vals())
        move_line.lot_id = self.lot

        with self.assertRaises(UserError) as cm:
            move_line.quantity = 10.0
            move._action_done()
        self.assertRegex(cm.exception.args[0], "avoid negative stock")

    def test_allow_positive_package(self):
        package = self.env["stock.quant.package"].create({"name": "test_package"})
        self.env["stock.quant"]._update_available_quantity(
            product_id=self.product,
            location_id=self.stock_location,
            quantity=10.0,
            package_id=package,
        )
        move = self.env["stock.move"].create(
            {
                "name": "test_negative",
                "location_id": self.stock_location.id,
                "location_dest_id": self.pack_location.id,
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 10.0,
            }
        )
        move_line = self.env["stock.move.line"].create(move._prepare_move_line_vals())
        move_line.package_id = package
        move_line.quantity = 10.0
        move._action_done()

    def test_prevent_negative_package(self):
        package = self.env["stock.quant.package"].create({"name": "test_package"})
        self.env["stock.quant"]._update_available_quantity(
            product_id=self.product,
            location_id=self.stock_location,
            quantity=10.0,
            package_id=package,
        )
        move = self.env["stock.move"].create(
            {
                "name": "test_negative",
                "location_id": self.stock_location.id,
                "location_dest_id": self.pack_location.id,
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 10.0,
            }
        )
        move_line = self.env["stock.move.line"].create(move._prepare_move_line_vals())

        with self.assertRaises(UserError) as cm:
            move_line.quantity = 10.0
            move._action_done()
        self.assertRegex(cm.exception.args[0], "avoid negative stock")
