# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import SQL

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


@tagged("post_install", "-at_install")
class TestStockDisassembly(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.result_a = cls.env["product.product"].create(
            {**cls.product_common_vals, "name": "Result A", "categ_id": cls.category_avco_auto.id, "standard_price": 30}
        )
        cls.result_b = cls.env["product.product"].create(
            {**cls.product_common_vals, "name": "Result B", "categ_id": cls.category_avco_auto.id, "standard_price": 5}
        )
        cls.result_c = cls.env["product.product"].create(
            {**cls.product_common_vals, "name": "Result C", "categ_id": cls.category_avco_auto.id, "standard_price": 1}
        )
        cls.waste = cls.env["product.product"].create(
            {**cls.product_common_vals, "name": "Waste", "categ_id": cls.category_avco_auto.id, "standard_price": 0}
        )

    def _disassembly(self, product, qty, lines, **vals):
        return self.env["stock.disassembly"].create(
            {
                "product_id": product.id,
                "product_qty": qty,
                "location_id": self.stock_location.id,
                "line_ids": [(0, 0, line) for line in lines],
                **vals,
            }
        )

    def _entry_lines(self, disassembly):
        return disassembly.account_move_id.line_ids

    def test_average_cost_by_reference_price(self):
        self._make_in_move(self.product_avco_auto, 10, unit_cost=10)
        disassembly = self._disassembly(
            self.product_avco_auto,
            2,
            [
                {"product_id": self.result_a.id, "quantity": 2},
                {"product_id": self.result_b.id, "quantity": 4},
            ],
        )
        self.assertEqual(disassembly.value, 20)
        disassembly.action_validate()

        self.assertEqual(disassembly.state, "done")
        self.assertTrue(disassembly.name.startswith("PVD/"))
        self.assertEqual(disassembly.source_value, 20)
        # weights 2 x 30 = 60 and 4 x 5 = 20
        line_a, line_b = disassembly.line_ids
        self.assertAlmostEqual(line_a.value, 15)
        self.assertAlmostEqual(line_b.value, 5)
        self.assertAlmostEqual(line_a.move_ids.value, 15)
        self.assertAlmostEqual(line_b.move_ids.value, 5)
        self.assertAlmostEqual(self.result_a.standard_price, 7.5)
        self.assertEqual(self.product_avco_auto.qty_available, 8)
        self.assertEqual(self.result_b.qty_available, 4)

        entry = disassembly.account_move_id
        self.assertEqual(entry.state, "posted")
        self.assertEqual(entry.journal_id, self.company.account_stock_journal_id)
        self.assertAlmostEqual(sum(entry.line_ids.mapped("debit")), 20)
        self.assertEqual(set(entry.line_ids.account_id.ids), {self.account_stock_valuation.id})
        # no automatic entry per stock move
        self.assertEqual(disassembly.move_ids.account_move_id, entry)
        self.assertEqual(disassembly.move_ids.mapped("reference"), [disassembly.name] * 3)

    def test_fifo_actual_cost_and_percent(self):
        self._make_in_move(self.product_fifo_auto, 5, unit_cost=10)
        self._make_in_move(self.product_fifo_auto, 5, unit_cost=20)
        disassembly = self._disassembly(
            self.product_fifo_auto,
            7,
            [
                {"product_id": self.result_a.id, "quantity": 1, "percent": 30},
                {"product_id": self.result_b.id, "quantity": 1, "percent": 70},
            ],
            allocation_method="percent",
        )
        disassembly.action_validate()
        # 5 x 10 + 2 x 20 from the FIFO layers
        self.assertAlmostEqual(disassembly.source_value, 90)
        self.assertAlmostEqual(disassembly.line_ids[0].value, 27)
        self.assertAlmostEqual(disassembly.line_ids[1].value, 63)

    def test_percent_must_add_up(self):
        self._make_in_move(self.product_avco_auto, 1, unit_cost=10)
        disassembly = self._disassembly(
            self.product_avco_auto,
            1,
            [{"product_id": self.result_a.id, "quantity": 1, "percent": 40}],
            allocation_method="percent",
        )
        with self.assertRaises(ValidationError):
            disassembly.action_validate()

    def test_rounding_on_last_line(self):
        self._make_in_move(self.product_avco_auto, 1, unit_cost=10)
        disassembly = self._disassembly(
            self.product_avco_auto,
            1,
            [
                {"product_id": self.result_a.id, "quantity": 1},
                {"product_id": self.result_b.id, "quantity": 1},
                {"product_id": self.result_c.id, "quantity": 1},
            ],
            allocation_method="quantity",
        )
        disassembly.action_validate()
        self.assertEqual(disassembly.line_ids.mapped("value"), [3.33, 3.33, 3.34])
        self.assertAlmostEqual(sum(disassembly.line_ids.move_ids.mapped("value")), 10)

    def test_fixed_value_first_and_scrap(self):
        self._make_in_move(self.product_avco_auto, 10, unit_cost=10)
        disassembly = self._disassembly(
            self.product_avco_auto,
            10,
            [
                {"product_id": self.result_a.id, "quantity": 6},
                # recoverable waste entering the stock at its net realisable value
                {"product_id": self.waste.id, "quantity": 2, "use_fixed_value": True, "fixed_value": 4},
                # scrap within the norm: no value
                {"product_id": self.waste.id, "quantity": 1, "line_type": "scrap"},
                # scrap above the norm: share of the value, booked as expense
                {"product_id": self.result_b.id, "quantity": 1, "line_type": "scrap", "over_norm": True},
            ],
            allocation_method="quantity",
        )
        disassembly.action_validate()
        product_line, waste_line, scrap_norm, scrap_over = disassembly.line_ids
        self.assertAlmostEqual(waste_line.value, 4)
        self.assertAlmostEqual(scrap_norm.value, 0)
        # 96 shared by quantity between 6 units in stock and 1 unit above the norm
        self.assertAlmostEqual(product_line.value, 82.29)
        self.assertAlmostEqual(scrap_over.value, 13.71)
        self.assertAlmostEqual(disassembly.over_norm_value, 13.71)
        self.assertEqual(scrap_norm.move_ids.location_dest_id, disassembly.scrap_location_id)
        self.assertEqual(self.waste.qty_available, 2)
        self.assertFalse(scrap_norm.move_ids.account_move_id)
        self.assertEqual(product_line.move_ids.account_move_id, disassembly.account_move_id)

        expense_lines = self._entry_lines(disassembly).filtered(lambda aml: aml.account_id == self.account_expense)
        self.assertAlmostEqual(sum(expense_lines.mapped("debit")), 13.71)
        stock_lines = self._entry_lines(disassembly).filtered(
            lambda aml: aml.account_id == self.account_stock_valuation
        )
        self.assertAlmostEqual(sum(stock_lines.mapped("credit")), 100)

    def test_loss_above_norm_needs_value(self):
        self._make_in_move(self.product_avco_auto, 1, unit_cost=10)
        disassembly = self._disassembly(
            self.product_avco_auto,
            1,
            [
                {"product_id": self.result_a.id, "quantity": 1},
                # reference price 0: the loss would get no value
                {"product_id": self.waste.id, "quantity": 1, "line_type": "scrap", "over_norm": True},
            ],
        )
        with self.assertRaises(UserError):
            disassembly.action_validate()

    def test_same_valuation_required(self):
        self._make_in_move(self.product_avco, 1, unit_cost=10)
        disassembly = self._disassembly(self.product_avco, 1, [{"product_id": self.result_a.id, "quantity": 1}])
        with self.assertRaises(ValidationError):
            disassembly.action_validate()

    def test_fixed_values_difference_to_last_line(self):
        self._make_in_move(self.product_avco_auto, 1, unit_cost=10)
        disassembly = self._disassembly(
            self.product_avco_auto,
            1,
            [
                {"product_id": self.result_a.id, "quantity": 1, "fixed_value": 6},
                {"product_id": self.result_b.id, "quantity": 1, "fixed_value": 3},
            ],
            allocation_method="fixed",
        )
        disassembly.action_validate()
        self.assertEqual(disassembly.line_ids.mapped("value"), [6, 4])

    def test_fixed_values_above_cost(self):
        self._make_in_move(self.product_avco_auto, 1, unit_cost=10)
        disassembly = self._disassembly(
            self.product_avco_auto,
            1,
            [
                {"product_id": self.result_a.id, "quantity": 1, "use_fixed_value": True, "fixed_value": 15},
                {"product_id": self.result_b.id, "quantity": 1},
            ],
        )
        with self.assertRaises(UserError):
            disassembly.action_validate()

    def test_not_enough_stock(self):
        self._make_in_move(self.product_avco_auto, 1, unit_cost=10)
        disassembly = self._disassembly(self.product_avco_auto, 2, [{"product_id": self.result_a.id, "quantity": 1}])
        with self.assertRaises(UserError):
            disassembly.action_validate()

    def test_validate_once(self):
        self._make_in_move(self.product_avco_auto, 2, unit_cost=10)
        disassembly = self._disassembly(self.product_avco_auto, 1, [{"product_id": self.result_a.id, "quantity": 1}])
        disassembly.action_validate()
        with self.assertRaises(UserError):
            disassembly.action_validate()
        self.assertEqual(self.product_avco_auto.qty_available, 1)

    def test_lots(self):
        tracked = self.env["product.product"].create(
            {**self.product_common_vals, "name": "Tracked", "categ_id": self.category_avco_auto.id, "tracking": "lot"}
        )
        tracked_result = self.env["product.product"].create(
            {
                **self.product_common_vals,
                "name": "Tracked Result",
                "categ_id": self.category_avco_auto.id,
                "tracking": "lot",
            }
        )
        lot = self.env["stock.lot"].create({"name": "L1", "product_id": tracked.id})
        self._make_in_move(tracked, 3, unit_cost=10, lot_ids=[lot])
        disassembly = self._disassembly(tracked, 1, [{"product_id": tracked_result.id, "quantity": 2}])
        with self.assertRaises(ValidationError):
            disassembly.action_validate()
        disassembly.lot_id = lot
        with self.assertRaises(ValidationError):
            disassembly.action_validate()
        disassembly.line_ids.lot_name = "R1"
        disassembly.action_validate()
        self.assertEqual(disassembly.move_ids.filtered("disassembly_line_id").move_line_ids.lot_id.name, "R1")
        self.assertEqual(disassembly.move_ids.filtered(lambda m: not m.disassembly_line_id).move_line_ids.lot_id, lot)

    def test_delete_done(self):
        self._make_in_move(self.product_avco_auto, 1, unit_cost=10)
        disassembly = self._disassembly(self.product_avco_auto, 1, [{"product_id": self.result_a.id, "quantity": 1}])
        disassembly.action_validate()
        with self.assertRaises(UserError):
            disassembly.unlink()


@tagged("post_install", "-at_install")
class TestStockDisassemblyRomania(TestStockValuationCommon):
    """Romanian chart: stock to stock entries, 34x only through 711."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # written in SQL: through the ORM the change of country loads a chart of accounts
        cls.env.cr.execute(
            SQL(
                "UPDATE res_company SET account_fiscal_country_id = %s WHERE id = %s",
                cls.env.ref("base.ro").id,
                cls.company.id,
            )
        )
        cls.company.invalidate_recordset(["account_fiscal_country_id"])

        def account(code, name, account_type):
            return cls.env["account.account"].create({"code": code, "name": name, "account_type": account_type})

        cls.acc_371 = account("371001", "Goods", "asset_current")
        cls.acc_301 = account("301001", "Raw materials", "asset_current")
        cls.acc_346 = account("346001", "Residual products", "asset_current")
        cls.acc_345 = account("345001", "Finished products", "asset_current")
        cls.acc_607 = account("607001", "Cost of goods sold", "expense")
        cls.acc_711 = account("711001", "Change in inventories", "income")

        def category(name, stock_account):
            return cls.env["product.category"].create(
                {
                    "name": name,
                    "property_valuation": "real_time",
                    "property_cost_method": "average",
                    "property_stock_valuation_account_id": stock_account.id,
                    "property_account_expense_categ_id": cls.acc_607.id,
                }
            )

        def product(name, categ):
            return cls.env["product.product"].create({**cls.product_common_vals, "name": name, "categ_id": categ.id})

        cls.goods = product("Goods", category("Goods", cls.acc_371))
        cls.goods_part = product("Goods part", category("Goods parts", cls.acc_371))
        cls.material = product("Material", category("Materials", cls.acc_301))
        cls.residual = product("Residual", category("Residual", cls.acc_346))
        cls.finished = product("Finished", category("Finished", cls.acc_345))

    def _disassembly(self, lines, source=None):
        source = source or self.goods
        self._make_in_move(source, 10, unit_cost=10)
        return self.env["stock.disassembly"].create(
            {
                "product_id": source.id,
                "product_qty": 1,
                "location_id": self.stock_location.id,
                "allocation_method": "quantity",
                "line_ids": [(0, 0, {"product_id": product.id, "quantity": 1}) for product in lines],
            }
        )

    def _balance(self, disassembly, account):
        lines = disassembly.account_move_id.line_ids.filtered(lambda aml: aml.account_id == account)
        return sum(lines.mapped("balance"))

    def test_goods_to_goods_and_residual(self):
        disassembly = self._disassembly([self.goods_part, self.residual])
        disassembly.action_validate()
        # 371 = 371 directly; 346 through 607 / 711
        self.assertAlmostEqual(self._balance(disassembly, self.acc_371), -5)
        self.assertAlmostEqual(self._balance(disassembly, self.acc_607), 5)
        self.assertAlmostEqual(self._balance(disassembly, self.acc_346), 5)
        self.assertAlmostEqual(self._balance(disassembly, self.acc_711), -5)
        goods_lines = disassembly.account_move_id.line_ids.filtered(lambda aml: aml.account_id == self.acc_371)
        # the lines on the same account are not netted
        self.assertEqual(len(goods_lines), 3)

    def test_goods_to_materials_needs_policy(self):
        disassembly = self._disassembly([self.material])
        with self.assertRaises(UserError):
            disassembly.action_validate()
        self.assertEqual(disassembly.state, "draft")
        self.company.disassembly_allow_reclassification = True
        disassembly.action_validate()
        self.assertAlmostEqual(self._balance(disassembly, self.acc_301), 10)
        self.assertAlmostEqual(self._balance(disassembly, self.acc_371), -10)

    def test_finished_products_to_materials_and_residual(self):
        disassembly = self._disassembly([self.material, self.residual], source=self.finished)
        disassembly.action_validate()
        # 301 = 345 directly; 346 through 711 = 345 and 346 = 711
        self.assertAlmostEqual(self._balance(disassembly, self.acc_301), 5)
        self.assertAlmostEqual(self._balance(disassembly, self.acc_345), -10)
        self.assertAlmostEqual(self._balance(disassembly, self.acc_346), 5)
        self.assertAlmostEqual(self._balance(disassembly, self.acc_711), 0)
        self.assertFalse(disassembly.account_move_id.line_ids.filtered(lambda aml: aml.account_id == self.acc_607))

    def test_residual_to_materials_refused(self):
        disassembly = self._disassembly([self.material], source=self.residual)
        with self.assertRaises(UserError):
            disassembly.action_validate()
        self.assertEqual(disassembly.state, "draft")
