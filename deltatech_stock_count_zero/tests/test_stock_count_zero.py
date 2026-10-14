# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.stock.models.stock_quant import StockQuant


@tagged("post_install", "-at_install")
class TestStockCountZero(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
            }
        )
        self.stock_location = self.env.ref("stock.stock_location_stock")

        # Create initial quant and apply it to have 10.0 in quantity
        self.quant = (
            self.env["stock.quant"]
            .with_context(inventory_mode=True)
            .create(
                {
                    "product_id": self.product.id,
                    "location_id": self.stock_location.id,
                    "inventory_quantity": 10.0,
                }
            )
        )
        self.quant.action_apply_inventory()
        self.assertEqual(self.quant.quantity, 10.0)

    def test_stock_count_zero_checked(self):
        """Test setting count to zero when 'set_count_zero' is checked in wizard"""
        # Create the wizard
        wizard = self.env["stock.request.count"].create(
            {
                "set_count_zero": True,
                "quant_ids": [(6, 0, self.quant.ids)],
            }
        )

        # Action the wizard
        wizard.action_request_count()

        # Invalidate cache to ensure we get fresh data from DB
        self.quant.invalidate_recordset(["quantity"])

        # Verify that quantity is now 0.0 (inventory_quantity is cleared after application)
        self.assertEqual(
            self.quant.quantity, 0.0, "The quantity should be set to 0.0 when 'set_count_zero' is checked."
        )

    def test_stock_count_zero_unchecked(self):
        """Test that count is NOT set to zero when 'set_count_zero' is unchecked"""
        # Create the wizard
        wizard = self.env["stock.request.count"].create(
            {
                "set_count_zero": False,
                "quant_ids": [(6, 0, self.quant.ids)],
            }
        )

        # Action the wizard
        wizard.action_request_count()

        # Invalidate cache
        self.quant.invalidate_recordset(["quantity"])

        # Verify that quantity is still 10.0
        self.assertEqual(
            self.quant.quantity, 10.0, "The quantity should not be changed when 'set_count_zero' is unchecked."
        )

    def test_stock_count_zero_outdated_opens_conflict(self):
        """An outdated quant returns the conflict wizard instead of silently skipping the adjustment"""
        wizard = self.env["stock.request.count"].create({"set_count_zero": True, "quant_ids": [(6, 0, self.quant.ids)]})

        def _compute_is_outdated(quants):
            quants.is_outdated = True

        with patch.object(StockQuant, "_compute_is_outdated", _compute_is_outdated):
            self.quant.invalidate_recordset(["is_outdated"])
            action = wizard.action_request_count()
        self.quant.invalidate_recordset(["is_outdated"])

        self.assertEqual(action.get("res_model"), "stock.inventory.conflict")
        self.assertEqual(action["context"]["default_quant_to_fix_ids"], self.quant.ids)
        self.assertEqual(self.quant.quantity, 10.0, "Nothing is applied before the conflict is solved")

        conflict = self.env["stock.inventory.conflict"].with_context(**action["context"]).create({})
        conflict.with_context(inventory_mode=True).action_keep_counted_quantity()
        self.assertEqual(self.quant.quantity, 0.0)

    def test_stock_count_zero_lot_only_selected_quant(self):
        """With lots, only the selected quant is set to zero, not the other lots of the location"""
        self.env.user.group_ids |= self.env.ref("stock.group_production_lot")
        product = self.env["product.product"].create({"name": "Lot Product", "is_storable": True, "tracking": "lot"})
        lot_1, lot_2 = self.env["stock.lot"].create(
            [{"name": "LOT-1", "product_id": product.id}, {"name": "LOT-2", "product_id": product.id}]
        )
        quants = (
            self.env["stock.quant"]
            .with_context(inventory_mode=True)
            .create(
                [
                    {
                        "product_id": product.id,
                        "location_id": self.stock_location.id,
                        "lot_id": lot.id,
                        "inventory_quantity": 5.0,
                    }
                    for lot in (lot_1, lot_2)
                ]
            )
        )
        quants.action_apply_inventory()
        quant_1, quant_2 = quants

        wizard = self.env["stock.request.count"].create({"set_count_zero": True, "quant_ids": [(6, 0, quant_1.ids)]})
        self.assertEqual(wizard._get_quants_to_count(), quants, "The standard request adds the sibling lots")
        wizard.action_request_count()

        quants.invalidate_recordset()
        self.assertEqual(quant_1.quantity, 0.0)
        self.assertEqual(quant_2.quantity, 5.0, "The lot that was not selected keeps its quantity")
        self.assertFalse(quant_2.inventory_quantity_set)

    def test_stock_count_zero_requires_stock_manager(self):
        """A stock user (not administrator) cannot set the count to zero"""
        stock_user = new_test_user(self.env, login="count_zero_user", groups="stock.group_stock_user")
        # the standard ACL gives the wizard to the administrators only; a database may open it to the
        # stock users (custom access right): the option to set the count to zero must stay restricted
        self.env["ir.model.access"].create(
            {
                "name": "request count stock user",
                "model_id": self.env.ref("stock.model_stock_request_count").id,
                "group_id": self.env.ref("stock.group_stock_user").id,
                "perm_read": True,
                "perm_write": True,
                "perm_create": True,
            }
        )
        Wizard = self.env["stock.request.count"].with_user(stock_user)
        with self.assertRaisesRegex(AccessError, "set_count_zero"):
            Wizard.create({"set_count_zero": True, "quant_ids": [(6, 0, self.quant.ids)]})

        wizard = self.env["stock.request.count"].create({"set_count_zero": True, "quant_ids": [(6, 0, self.quant.ids)]})
        with self.assertRaisesRegex(AccessError, "inventory administrator"):
            wizard.with_user(stock_user).action_request_count()
        self.assertEqual(self.quant.quantity, 10.0)

        # the standard request count still works for the stock user
        wizard = Wizard.create({"quant_ids": [(6, 0, self.quant.ids)], "user_id": stock_user.id})
        wizard.action_request_count()
        self.assertEqual(self.quant.user_id, stock_user)
        self.assertEqual(self.quant.quantity, 10.0)
