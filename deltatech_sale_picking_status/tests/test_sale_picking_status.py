import importlib.util

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase
from odoo.tools.misc import file_path


def _load_migration():
    path = file_path("deltatech_sale_picking_status/migrations/20.0.2.0.0/post-migration.py")
    spec = importlib.util.spec_from_file_location("deltatech_sale_picking_status_post_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged("post_install", "-at_install")
class TestStockPickingAndSaleOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Test Product A", "type": "consu", "is_storable": True, "list_price": 150}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Test Product B", "type": "consu", "is_storable": True, "list_price": 150}
        )
        stock_location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(cls.product_a, stock_location, 1000)
        cls.env["stock.quant"]._update_available_quantity(cls.product_b, stock_location, 1000)
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product_a.id, "product_uom_qty": 1.0}),
                    (0, 0, {"product_id": cls.product_b.id, "product_uom_qty": 2.0}),
                ],
            }
        )

    def _deliver(self, quantities=None):
        picking = self.sale_order.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = (quantities or {}).get(move.product_id, move.product_uom_qty)
        picking.move_ids.picked = True
        res = picking.button_validate()
        if isinstance(res, dict) and res.get("res_model") == "stock.backorder.confirmation":
            Form.from_action(self.env, res).save().process()
        return picking

    def test_delivery_status_flow(self):
        self.assertFalse(self.sale_order.delivery_status, "A quotation has no delivery status")
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.delivery_status, "pending")

        self._deliver({self.product_a: 1.0, self.product_b: 1.0})
        self.assertEqual(self.sale_order.delivery_status, "partial")

        self._deliver()
        self.assertEqual(self.sale_order.delivery_status, "full")

        # the tracking values are written at the end of the transaction
        self.env.flush_all()
        self.env.cr.precommit.run()
        tracked = self.sale_order.message_ids.tracking_value_ids.filtered(
            lambda t: t.field_id.name == "delivery_status"
        )
        self.assertTrue(tracked, "The delivery status changes are tracked in the chatter")

    def test_delivery_status_cancel_pickings(self):
        self.sale_order.action_confirm()
        self.sale_order.picking_ids.action_cancel()
        self.assertEqual(self.sale_order.state, "sale")
        self.assertFalse(self.sale_order.delivery_status)

    def test_search_filters(self):
        self.sale_order.action_confirm()
        in_progress = self.env["sale.order"].search(
            [("delivery_status", "in", ("pending", "started", "partial")), ("id", "=", self.sale_order.id)]
        )
        self.assertEqual(in_progress, self.sale_order)
        arch = self.env["sale.order"].get_view(self.env.ref("sale.view_sales_order_filter").id, "search")["arch"]
        for name in ("pickings_in_progress", "delivery_partial", "pickings_done", "delivery_status_groupby"):
            self.assertIn(f'name="{name}"', arch)

    def test_migration_convert(self):
        migration = _load_migration()
        self.assertEqual(
            migration.convert_domain("[('picking_status', '=', 'done')]"),
            "[('delivery_status', '=', 'full')]",
        )
        self.assertEqual(
            migration.convert_domain('["&", ["picking_status", "=", "in_progress"], ["state", "=", "sale"]]'),
            "[\"&\", ('delivery_status', 'in', ['pending', 'started', 'partial']), [\"state\", \"=\", \"sale\"]]",
        )
        self.assertEqual(
            migration.convert_domain("[('picking_status', '!=', 'in_progress')]"),
            "[('delivery_status', 'not in', ['pending', 'started', 'partial'])]",
        )
        self.assertEqual(
            migration.convert_field("{'group_by': ['picking_status']}"),
            "{'group_by': ['delivery_status']}",
        )

    def test_migration_filters(self):
        migration = _load_migration()
        favorite = self.env["ir.filters"].create(
            {"name": "Old favorite", "model_id": "sale.order", "domain": "[]", "context": "{}"}
        )
        export = self.env["ir.exports"].create(
            {"name": "Old export", "resource": "sale.order", "export_fields": [(0, 0, {"name": "name"})]}
        )
        # the old field no longer exists: write the legacy values directly
        self.env.cr.execute(
            "UPDATE ir_filters SET domain = %s, context = %s WHERE id = %s",
            ("[('picking_status', '=', 'done')]", "{'group_by': ['picking_status']}", favorite.id),
        )
        self.env.cr.execute("UPDATE ir_exports_line SET name = 'picking_status' WHERE export_id = %s", (export.id,))
        self.env.invalidate_all()

        migration.migrate(self.env.cr, "19.0.1.0.1")
        self.env.invalidate_all()

        self.assertEqual(favorite.domain, "[('delivery_status', '=', 'full')]")
        self.assertEqual(favorite.context, "{'group_by': ['delivery_status']}")
        self.assertEqual(export.export_fields.name, "delivery_status")
        # the rewritten favorite is a valid domain on the standard field
        self.env["sale.order"].search(favorite._get_eval_domain())
