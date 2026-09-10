# ©  2015-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestInventoryLineValue(TransactionCase):
    """Snapshotul valoric al liniei de inventar: cost unitar, valoare teoretica,
    valoare numarata, diferenta estimata si valoarea efectiv postata."""

    def setUp(self):
        super().setUp()
        self.location = self.env["stock.location"].create({"name": "Value Loc", "usage": "internal"})
        self.product = self.env["product.product"].create(
            {"name": "Value Product", "is_storable": True, "standard_price": 25.0}
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "quantity": 10.0,
            }
        )
        self.inventory = self.env["stock.inventory"].create(
            {
                "name": "INV/VALUE",
                "location_ids": [(6, 0, [self.location.id])],
                "product_ids": [(6, 0, [self.product.id])],
            }
        )

    def _start(self):
        self.inventory.action_start()
        line = self.inventory.line_ids.filtered(lambda ln: ln.product_id == self.product)
        self.assertEqual(len(line), 1)
        return line

    def test_snapshot_on_line_generation(self):
        line = self._start()
        self.assertEqual(line.unit_value, 25.0)
        self.assertEqual(line.theoretical_qty, 10.0)
        self.assertEqual(line.theoretical_value, 250.0)
        # Cantitatea numarata e preumpluta cu stocul, deci nu exista diferenta
        self.assertEqual(line.counted_value, 250.0)
        self.assertEqual(line.diff_value, 0.0)
        self.assertEqual(line.posted_value, 0.0)

    def test_diff_value_visible_before_validation(self):
        line = self._start()
        line.product_qty = 8.0
        self.assertEqual(line.counted_value, 200.0)
        self.assertEqual(line.diff_value, -50.0)
        self.assertEqual(self.inventory.total_diff_value, -50.0)
        # Nimic nu s-a postat inca
        self.assertEqual(self.inventory.total_posted_value, 0.0)

    def test_posted_value_after_validation(self):
        line = self._start()
        line.product_qty = 8.0
        self.inventory.action_validate()

        self.assertEqual(self.inventory.state, "done")
        move = self.inventory.move_ids
        self.assertEqual(len(move), 1)
        self.assertEqual(move.inventory_line_id, line, "Mișcarea trebuie legata de linia care a generat-o")
        self.assertEqual(line.posted_value, -abs(move.value))
        self.assertEqual(self.inventory.total_posted_value, line.posted_value)

    def test_posted_value_positive_on_surplus(self):
        line = self._start()
        line.product_qty = 12.0
        self.assertEqual(line.diff_value, 50.0)
        self.inventory.action_validate()
        self.assertEqual(line.posted_value, abs(self.inventory.move_ids.value))
        self.assertGreater(line.posted_value, 0.0)

    def test_refresh_button_resnapshots_unit_value(self):
        line = self._start()
        self.product.standard_price = 30.0
        line.action_refresh_quantity()
        self.assertEqual(line.unit_value, 30.0)
        self.assertEqual(line.theoretical_value, 300.0)

    def test_operator_without_manager_group_can_generate_lines(self):
        """unit_value e restrans la managerii de stoc, dar liniile sunt generate de operatori."""
        operator = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Inv operator",
                    "login": "inv_operator_value",
                    "group_ids": [
                        (
                            6,
                            0,
                            [
                                self.env.ref("stock.group_stock_user").id,
                                self.env.ref("deltatech_stock_inventory.group_view_inventory_button").id,
                            ],
                        )
                    ],
                }
            )
        )
        inventory = self.inventory.with_user(operator)
        inventory.action_start()
        line = inventory.line_ids.filtered(lambda ln: ln.product_id == self.product)
        self.assertEqual(line.sudo().unit_value, 25.0)
        self.assertEqual(line.sudo().theoretical_value, 250.0)
