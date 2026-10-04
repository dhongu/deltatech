# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged

from odoo.addons.stock.models.stock_picking import StockPicking as BaseStockPicking

GROUP = "deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit"


@tagged("post_install", "-at_install")
class TestPickingRestrictEntryExit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.wh = cls.env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        cls.wh2 = cls.env["stock.warehouse"].create(
            {"name": "Test WH Restrict 2", "code": "TWR2", "company_id": cls.company.id}
        )
        cls.stock_loc = cls.wh.lot_stock_id
        cls.shelf_loc = cls.env["stock.location"].create(
            {"name": "Test Shelf", "location_id": cls.stock_loc.id, "usage": "internal"}
        )
        cls.supplier_loc = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_loc = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {"name": "Test Restrict Product", "type": "consu", "is_storable": True}
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock_loc, 100.0)
        cls.user = cls.env["res.users"].create(
            {
                "name": "Restricted Stock User",
                "login": "restricted_stock_user",
                "group_ids": [(6, 0, [cls.env.ref("stock.group_stock_manager").id])],
            }
        )
        # When sale_stock / purchase_stock are installed (e.g. alongside other addons on CI), the module
        # requires every delivery/receipt move to be linked to an order line: link them to draft orders.
        move_fields = cls.env["stock.move"]._fields
        cls.sale_line = cls.purchase_line = False
        partner = cls.env["res.partner"].create({"name": "Test Restrict Partner"})
        if "sale_line_id" in move_fields:
            order = cls.env["sale.order"].create(
                {"partner_id": partner.id, "order_line": [(0, 0, {"product_id": cls.product.id, "product_uom_qty": 5})]}
            )
            cls.sale_line = order.order_line
        if "purchase_line_id" in move_fields:
            order = cls.env["purchase.order"].create(
                {"partner_id": partner.id, "order_line": [(0, 0, {"product_id": cls.product.id, "product_qty": 5})]}
            )
            cls.purchase_line = order.order_line
        cls.privileged_user = cls.env["res.users"].create(
            {
                "name": "Privileged Stock User",
                "login": "privileged_stock_user",
                "group_ids": [(6, 0, [cls.env.ref("stock.group_stock_manager").id, cls.env.ref(GROUP).id])],
            }
        )

    def _make_picking(
        self, picking_type, location, location_dest, qty_demand=5.0, qty_done=None, link_order=True, **extra
    ):
        move_vals = {
            "product_id": self.product.id,
            "product_uom_qty": qty_demand,
            "product_uom": self.product.uom_id.id,
            "location_id": location.id,
            "location_dest_id": location_dest.id,
        }
        if link_order and picking_type.code == "outgoing" and self.sale_line:
            move_vals["sale_line_id"] = self.sale_line.id
        if link_order and picking_type.code == "incoming" and self.purchase_line:
            move_vals["purchase_line_id"] = self.purchase_line.id
        vals = {
            "picking_type_id": picking_type.id,
            "location_id": location.id,
            "location_dest_id": location_dest.id,
            "move_ids": [(0, 0, move_vals)],
        }
        vals.update(extra)
        picking = self.env["stock.picking"].create(vals)
        picking.action_confirm()
        if qty_done is not None:
            picking.move_ids.write({"quantity": qty_done, "picked": True})
        return picking

    def _receipt(self, **kw):
        return self._make_picking(self.wh.in_type_id, self.supplier_loc, self.stock_loc, **kw)

    def _delivery(self, **kw):
        return self._make_picking(self.wh.out_type_id, self.stock_loc, self.customer_loc, **kw)

    def _internal(self, dest, **kw):
        return self._make_picking(self.wh.int_type_id, self.stock_loc, dest, **kw)

    # ------------------------------------------------------------------
    # security group
    # ------------------------------------------------------------------
    def test_group_assignment(self):
        self.assertTrue(self.env.ref("base.user_admin").has_group(GROUP))
        self.assertFalse(self.user.has_group(GROUP))
        self.assertTrue(self.privileged_user.has_group(GROUP))

    # ------------------------------------------------------------------
    # button_validate
    # ------------------------------------------------------------------
    def test_validate_receipt_ok(self):
        picking = self._receipt(qty_done=5.0)
        picking.with_user(self.user).button_validate()
        self.assertEqual(picking.state, "done")

    def test_validate_receipt_qty_greater_restricted(self):
        picking = self._receipt(qty_done=7.0)
        with self.assertRaisesRegex(UserError, "greater than the quantity ordered"):
            picking.with_user(self.user).button_validate()

    def test_validate_delivery_qty_greater_restricted(self):
        picking = self._delivery(qty_done=7.0)
        with self.assertRaisesRegex(UserError, "greater than the quantity ordered"):
            picking.with_user(self.user).button_validate()

    def test_validate_receipt_qty_greater_privileged(self):
        picking = self._receipt(qty_done=7.0)
        picking.with_user(self.privileged_user).button_validate()
        self.assertEqual(picking.state, "done")

    def test_validate_zero_qty_line_ignored(self):
        picking = self._receipt(qty_done=5.0)
        # a line with no demand and no quantity (e.g. added and removed in barcode) is skipped
        self.env["stock.move"].create(
            {
                "picking_id": picking.id,
                "product_id": self.product.id,
                "product_uom_qty": 0.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.supplier_loc.id,
                "location_dest_id": self.stock_loc.id,
            }
        )
        picking.with_user(self.user).button_validate()
        self.assertEqual(picking.state, "done")

    def test_validate_return_not_restricted(self):
        origin = self._receipt(qty_done=5.0)
        origin.button_validate()
        picking = self._delivery(qty_done=7.0, return_id=origin.id)
        picking.with_user(self.user).button_validate()
        self.assertEqual(picking.state, "done")

    def test_validate_backorder_not_restricted(self):
        origin = self._receipt(qty_done=5.0)
        origin.button_validate()
        picking = self._receipt(qty_done=7.0, backorder_id=origin.id)
        picking.with_user(self.user).button_validate()
        self.assertEqual(picking.state, "done")

    def test_validate_batch_with_backorder_still_restricted(self):
        # a backorder in the selection must not exempt the other pickings validated with it
        origin = self._receipt(qty_done=5.0)
        origin.button_validate()
        backorder = self._receipt(qty_done=5.0, backorder_id=origin.id)
        picking = self._receipt(qty_done=7.0)
        with self.assertRaisesRegex(UserError, "greater than the quantity ordered"):
            (backorder | picking).with_user(self.user).button_validate()

    def test_validate_internal_same_warehouse(self):
        picking = self._internal(self.shelf_loc, qty_done=7.0)
        picking.with_user(self.user).button_validate()
        self.assertEqual(picking.state, "done")

    def test_validate_internal_other_warehouse(self):
        picking = self._internal(self.wh2.lot_stock_id, qty_done=7.0)
        with self.assertRaisesRegex(UserError, "greater than the quantity ordered"):
            picking.with_user(self.user).button_validate()

    def _fake_move_field(self, name):
        move_cls = type(self.env["stock.move"])
        fields = move_cls._fields
        if name not in fields:
            fields = {**fields, name: fields["picking_id"]}
        return (
            patch.object(move_cls, "_fields", fields),
            patch.object(move_cls, name, False, create=True),
        )

    def test_validate_delivery_without_sale_line(self):
        picking = self._delivery(qty_done=5.0, link_order=False)
        p1, p2 = self._fake_move_field("sale_line_id")
        with p1, p2, self.assertRaisesRegex(UserError, "not linked to a sale order line"):
            picking.with_user(self.user).button_validate()

    def test_validate_receipt_without_purchase_line(self):
        picking = self._receipt(qty_done=5.0, link_order=False)
        p1, p2 = self._fake_move_field("purchase_line_id")
        with p1, p2, self.assertRaisesRegex(UserError, "not linked to a purchase order line"):
            picking.with_user(self.user).button_validate()

    # ------------------------------------------------------------------
    # write (save-time checks on move_ids commands)
    # ------------------------------------------------------------------
    def _write(self, picking, commands, user=None):
        picking = picking.with_user(user or self.user)
        with patch.object(BaseStockPicking, "write", autospec=True, return_value=True) as base_write:
            picking.write({"move_ids": commands})
        return base_write

    def test_write_existing_line_qty_greater(self):
        picking = self._receipt()
        move = picking.move_ids
        with self.assertRaisesRegex(UserError, "You cannot save the picking"):
            self._write(picking, [(1, move.id, {"quantity": 7.0})])

    def test_write_existing_line_qty_ok(self):
        picking = self._receipt()
        move = picking.move_ids
        base_write = self._write(picking, [(1, move.id, {"quantity": 3.0}), (4, move.id), (1, move.id, {"picked": 1})])
        base_write.assert_called_once()

    def test_write_existing_line_internal_same_warehouse(self):
        picking = self._internal(self.shelf_loc)
        base_write = self._write(picking, [(1, picking.move_ids.id, {"quantity": 7.0})])
        base_write.assert_called_once()

    def test_write_existing_line_internal_other_warehouse(self):
        picking = self._internal(self.wh2.lot_stock_id)
        with self.assertRaisesRegex(UserError, "You cannot save the picking"):
            self._write(picking, [(1, picking.move_ids.id, {"quantity": 7.0})])

    def _virtual(self, picking_type, location, location_dest, quantity, demand):
        return (
            0,
            "virtual_1",
            {
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
                "quantity": quantity,
                "product_uom_qty": demand,
            },
        )

    def test_write_new_line_incoming_restricted(self):
        picking = self._receipt()
        command = self._virtual(self.wh.in_type_id, self.supplier_loc, self.stock_loc, 1.0, 1.0)
        with self.assertRaisesRegex(UserError, "manually add moves"):
            self._write(picking, [command])

    def test_write_new_line_outgoing_restricted(self):
        picking = self._delivery()
        command = self._virtual(self.wh.out_type_id, self.stock_loc, self.customer_loc, 1.0, 1.0)
        with self.assertRaisesRegex(UserError, "manually add moves"):
            self._write(picking, [command])

    def test_write_new_line_incoming_privileged(self):
        picking = self._receipt()
        command = self._virtual(self.wh.in_type_id, self.supplier_loc, self.stock_loc, 1.0, 2.0)
        base_write = self._write(picking, [command], user=self.privileged_user)
        base_write.assert_called_once()

    def test_write_new_line_incoming_privileged_qty_greater(self):
        picking = self._receipt()
        command = self._virtual(self.wh.in_type_id, self.supplier_loc, self.stock_loc, 3.0, 2.0)
        with self.assertRaisesRegex(UserError, "quantity done is greater than the quantity needed"):
            self._write(picking, [command], user=self.privileged_user)

    def test_write_new_line_internal_same_warehouse(self):
        picking = self._internal(self.shelf_loc)
        command = self._virtual(self.wh.int_type_id, self.stock_loc, self.shelf_loc, 9.0, 2.0)
        base_write = self._write(picking, [command])
        base_write.assert_called_once()

    def test_write_new_line_internal_other_warehouse(self):
        picking = self._internal(self.wh2.lot_stock_id)
        command = self._virtual(self.wh.int_type_id, self.stock_loc, self.wh2.lot_stock_id, 9.0, 2.0)
        with self.assertRaisesRegex(UserError, "quantity done is greater than the quantity needed"):
            self._write(picking, [command])

    def test_write_new_line_without_virtual_id(self):
        # a CREATE command with 0 instead of a virtual id and without the line's picking type / locations
        # (e.g. from code) is still a new line, checked against the picking's type
        picking = self._receipt()
        command = Command.create({"product_id": self.product.id, "quantity": 1.0, "product_uom_qty": 1.0})
        with self.assertRaisesRegex(UserError, "manually add moves"):
            self._write(picking, [command])

    def test_write_existing_line_list_command(self):
        # JSON-RPC delivers the commands as lists, not tuples
        picking = self._receipt()
        with self.assertRaisesRegex(UserError, "You cannot save the picking"):
            self._write(picking, [[1, picking.move_ids.id, {"quantity": 7.0}]])

    def test_write_existing_line_demand_changed(self):
        # the quantity is compared with the demand sent in the same save
        picking = self._receipt()
        base_write = self._write(
            picking, [Command.update(picking.move_ids.id, {"quantity": 7.0, "product_uom_qty": 8.0})]
        )
        base_write.assert_called_once()

    def test_write_commands_without_values(self):
        picking = self._receipt()
        move = picking.move_ids
        commands = [
            Command.delete(move.id),
            Command.unlink(move.id),
            Command.link(move.id),
            Command.clear(),
            Command.set(move.ids),
            Command.update(move.id, {"picked": True}),
        ]
        base_write = self._write(picking, commands)
        base_write.assert_called_once()

    def test_write_form_existing_line_qty_greater(self):
        # end to end, without mocking the base write: the commands built by the form view
        picking = self._receipt()
        with self.assertRaisesRegex(UserError, "You cannot save the picking"):
            with Form(picking.with_user(self.user)) as picking_form:
                with picking_form.move_ids.edit(0) as line:
                    line.quantity = 7.0
        self.assertEqual(picking.move_ids.quantity, 5.0)

    def test_write_form_existing_line_qty_ok(self):
        picking = self._receipt()
        with Form(picking.with_user(self.user)) as picking_form:
            with picking_form.move_ids.edit(0) as line:
                line.quantity = 3.0
        self.assertEqual(picking.move_ids.quantity, 3.0)

    def test_write_form_new_line_incoming_restricted(self):
        picking = self._receipt()
        with self.assertRaisesRegex(UserError, "manually add moves"):
            with Form(picking.with_user(self.user)) as picking_form:
                with picking_form.move_ids.new() as line:
                    line.product_id = self.product
                    line.quantity = 1.0
        self.assertEqual(len(picking.move_ids), 1)

    def test_write_form_new_line_internal_same_warehouse(self):
        picking = self._internal(self.shelf_loc)
        with Form(picking.with_user(self.user)) as picking_form:
            with picking_form.move_ids.new() as line:
                line.product_id = self.product
                line.quantity = 4.0
        self.assertEqual(len(picking.move_ids), 2)

    def test_write_without_move_commands(self):
        picking = self._receipt()
        picking.with_user(self.user).write({"origin": "TEST-ORIGIN"})
        self.assertEqual(picking.origin, "TEST-ORIGIN")
