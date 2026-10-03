import importlib.util

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase
from odoo.tools.misc import file_path


def _load_migration():
    path = file_path("deltatech_purchase_picking_status/migrations/20.0.2.0.0/post-migration.py")
    spec = importlib.util.spec_from_file_location("deltatech_purchase_picking_status_post_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged("post_install", "-at_install")
class TestPurchaseOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "is_storable": True, "standard_price": 50.0}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [(0, 0, {"product_id": cls.product.id, "product_qty": 10, "price_unit": 100})],
            }
        )

    def _receive(self, quantity=None):
        picking = self.purchase_order.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))
        for move in picking.move_ids:
            move.quantity = quantity if quantity is not None else move.product_uom_qty
        picking.move_ids.picked = True
        res = picking.button_validate()
        if isinstance(res, dict) and res.get("res_model") == "stock.backorder.confirmation":
            Form.from_action(self.env, res).save().process()
        return picking

    def test_receipt_status_flow(self):
        self.assertFalse(self.purchase_order.receipt_status, "A request for quotation has no receipt status")
        self.purchase_order.button_confirm()
        self.assertEqual(self.purchase_order.receipt_status, "pending")

        self._receive(4)
        self.assertEqual(self.purchase_order.receipt_status, "partial")

        self._receive()
        self.assertEqual(self.purchase_order.receipt_status, "full")

        # the tracking values are written at the end of the transaction
        self.env.flush_all()
        self.env.cr.precommit.run()
        tracked = self.purchase_order.message_ids.tracking_value_ids.filtered(
            lambda t: t.field_id.name == "receipt_status"
        )
        self.assertTrue(tracked, "The receipt status changes are tracked in the chatter")

    def test_receipt_status_cancel_pickings(self):
        self.purchase_order.button_confirm()
        self.purchase_order.picking_ids.action_cancel()
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertFalse(self.purchase_order.receipt_status)

    def test_search_filters(self):
        self.purchase_order.button_confirm()
        in_progress = self.env["purchase.order"].search(
            [("receipt_status", "in", ("pending", "partial")), ("id", "=", self.purchase_order.id)]
        )
        self.assertEqual(in_progress, self.purchase_order)
        view = self.env.ref("purchase.purchase_order_view_search")
        arch = self.env["purchase.order"].get_view(view.id, "search")["arch"]
        for name in ("pickings_in_progress", "receipt_partial", "pickings_done", "receipt_status_groupby"):
            self.assertIn(f'name="{name}"', arch)

    def test_migration_convert(self):
        migration = _load_migration()
        self.assertEqual(
            migration.convert_domain("[('picking_status', '=', 'done')]"),
            "[('receipt_status', '=', 'full')]",
        )
        self.assertEqual(
            migration.convert_domain('["&", ["picking_status", "=", "in_progress"], ["state", "=", "purchase"]]'),
            "[\"&\", ('receipt_status', 'in', ['pending', 'partial']), [\"state\", \"=\", \"purchase\"]]",
        )
        self.assertEqual(
            migration.convert_domain("[('picking_status', '!=', 'in_progress')]"),
            "[('receipt_status', 'not in', ['pending', 'partial'])]",
        )
        self.assertEqual(
            migration.convert_field("{'group_by': ['picking_status']}"),
            "{'group_by': ['receipt_status']}",
        )

    def test_migration_filters(self):
        migration = _load_migration()
        favorite = self.env["ir.filters"].create(
            {"name": "Old favorite", "model_id": "purchase.order", "domain": "[]", "context": "{}"}
        )
        export = self.env["ir.exports"].create(
            {"name": "Old export", "resource": "purchase.order", "export_fields": [(0, 0, {"name": "name"})]}
        )
        # the old field no longer exists: write the legacy values directly
        self.env.cr.execute(
            "UPDATE ir_filters SET domain = %s, context = %s WHERE id = %s",
            ("[('picking_status', '=', 'done')]", "{'group_by': ['picking_status']}", favorite.id),
        )
        self.env.cr.execute("UPDATE ir_exports_line SET name = 'picking_status' WHERE export_id = %s", (export.id,))
        self.env.invalidate_all()

        migration.migrate(self.env.cr, "20.0.1.0.1")
        self.env.invalidate_all()

        self.assertEqual(favorite.domain, "[('receipt_status', '=', 'full')]")
        self.assertEqual(favorite.context, "{'group_by': ['receipt_status']}")
        self.assertEqual(export.export_fields.name, "receipt_status")
        # the rewritten favorite is a valid domain on the standard field
        self.env["purchase.order"].search(favorite._get_eval_domain())
