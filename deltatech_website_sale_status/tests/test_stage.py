# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleStage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Stage Customer"})
        cls.storable = cls.env["product.product"].create(
            {"name": "Stage Storable", "type": "consu", "is_storable": True, "list_price": 10}
        )
        cls.goods = cls.env["product.product"].create(
            {"name": "Stage Goods", "type": "consu", "is_storable": False, "list_price": 10}
        )
        cls.service = cls.env["product.product"].create({"name": "Stage Service", "type": "service", "list_price": 10})
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.website = cls.env["website"].search([], limit=1) or cls.env["website"].create({"name": "Stage Website"})
        cls._set_detailed_stage(True)

    @classmethod
    def _set_detailed_stage(cls, value):
        cls.env["ir.config_parameter"].sudo().set_param(
            "deltatech_website_sale_status.detailed_stage", "True" if value else False
        )

    def _create_order(self, product, qty=1.0, **vals):
        values = {
            "partner_id": self.partner.id,
            "warehouse_id": self.warehouse.id,
            "order_line": [(0, 0, {"product_id": product.id, "product_uom_qty": qty})],
        }
        values.update(vals)
        return self.env["sale.order"].create(values)

    def _put_in_stock(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(product, self.warehouse.lot_stock_id, qty)

    def _deliver(self, picking):
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.move_ids.picked = True
        picking.with_context(skip_backorder=True, skip_sms=True).button_validate()

    # ------------------------------------------------------------------
    # _compute_stage
    # ------------------------------------------------------------------
    def test_stage_backend_quotation_in_process(self):
        order = self._create_order(self.storable)
        self.assertEqual(order.stage, "in_process")

    def test_stage_website_draft_is_empty(self):
        order = self._create_order(self.storable, website_id=self.website.id)
        self.assertFalse(order.stage)

    def test_stage_website_sent(self):
        order = self._create_order(self.storable, website_id=self.website.id)
        order.action_quotation_sent()
        self.assertEqual(order.state, "sent")
        self.assertEqual(order.stage, "placed")

    def test_stage_backend_sent_in_process(self):
        order = self._create_order(self.storable)
        order.action_quotation_sent()
        self.assertEqual(order.state, "sent")
        self.assertEqual(order.stage, "in_process")

    def test_stage_canceled(self):
        order = self._create_order(self.storable)
        order._action_cancel()
        self.assertEqual(order.state, "cancel")
        self.assertEqual(order.stage, "canceled")

    def test_stage_waiting_without_stock(self):
        order = self._create_order(self.storable, qty=5)
        order.action_confirm()
        self.assertEqual(order.picking_ids.state, "confirmed")
        self.assertEqual(order.stage, "waiting")

    def test_stage_to_be_delivery_with_stock(self):
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=5)
        order.action_confirm()
        self.assertEqual(order.picking_ids.state, "assigned")
        self.assertEqual(order.stage, "to_be_delivery")

    def test_stage_postponed(self):
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=5)
        order.action_confirm()
        order.picking_ids.postponed = True
        self.assertTrue(order.postponed_delivery)
        self.assertEqual(order.stage, "postponed")
        order.picking_ids.postponed = False
        self.assertEqual(order.stage, "to_be_delivery")

    def test_stage_delivered_after_validation(self):
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=5)
        order.action_confirm()
        self._deliver(order.picking_ids)
        self.assertEqual(order.picking_ids.state, "done")
        self.assertEqual(order.stage, "delivered")

    def test_stage_delivered_partial_without_backorder(self):
        """All pickings done or canceled -> delivered, even with quantities left."""
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=5)
        order.action_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity = 2
        picking.move_ids.picked = True
        picking.with_context(cancel_backorder=True, skip_sms=True)._action_done()
        self.assertEqual(order.order_line.qty_to_deliver, 3)
        self.assertTrue(all(p.state in ("done", "cancel") for p in order.picking_ids))
        self.assertEqual(order.stage, "delivered")

    def test_stage_service_only_delivered(self):
        order = self._create_order(self.service, qty=1)
        order.action_confirm()
        self.assertFalse(order.picking_ids)
        self.assertEqual(order.stage, "delivered")

    def test_stage_in_delivery_from_delivery_state(self):
        """Non storable goods: nothing to deliver in stock terms, the parcel is on its way."""
        order = self._create_order(self.goods, qty=1)
        order.action_confirm()
        picking = order.picking_ids
        self.assertTrue(picking)
        self.assertEqual(order.stage, "delivered")
        picking.delivery_state = "in_transit"
        self.assertEqual(order.stage, "in_delivery")

    def test_stage_rfq_with_sent_purchase(self):
        if "purchase_order_count" not in self.env["sale.order"]._fields:
            self.skipTest("sale_purchase is not installed")
        vendor = self.env["res.partner"].create({"name": "Stage Vendor"})
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": vendor.id,
                "order_line": [(0, 0, {"product_id": self.storable.id, "product_qty": 1, "price_unit": 1})],
            }
        )
        purchase.write({"state": "sent"})
        order = self._create_order(self.storable, qty=5)
        order.action_confirm()
        order.picking_ids.action_cancel()
        order.picking_ids.unlink()
        sale_order_class = type(order)
        with patch.object(sale_order_class, "_get_purchase_orders", lambda self: purchase):
            order.invalidate_recordset(["purchase_order_count"])
            order._compute_stage()
            self.assertEqual(order.stage, "rfq")

    def test_action_confirm_computes_stage(self):
        order = Form(self.env["sale.order"])
        order.partner_id = self.partner
        with order.order_line.new() as line:
            line.product_id = self.storable
            line.product_uom_qty = 1
        order = order.save()
        order.action_confirm()
        self.assertEqual(order.stage, "waiting")

    # ------------------------------------------------------------------
    # stage from the carrier status (delivery_state) of the transfer
    # ------------------------------------------------------------------
    def _confirmed_goods_order(self):
        order = self._create_order(self.goods, qty=1)
        order.action_confirm()
        return order, order.picking_ids

    def test_picking_write_in_delivery_states(self):
        for delivery_state in ("in_transit", "in_warehouse", "in_delivery"):
            order, picking = self._confirmed_goods_order()
            picking.write({"delivery_state": delivery_state})
            self.assertEqual(order.stage, "in_delivery", delivery_state)

    def test_picking_write_delivered(self):
        order, picking = self._confirmed_goods_order()
        picking.write({"delivery_state": "in_transit"})
        picking.write({"delivery_state": "delivered"})
        self.assertEqual(order.stage, "delivered")

    def test_picking_write_pre_advice(self):
        order, picking = self._confirmed_goods_order()
        picking.write({"delivery_state": "pre_advice"})
        self.assertEqual(picking.delivery_state, "pre_advice")
        self.assertEqual(order.stage, "pre_advice")

    def test_picking_delivery_state_storable(self):
        """Storable products: the order follows the parcel, not only the stock moves.

        An AWB on a ready transfer is `pre_advice`, a parcel with the carrier is
        `in_delivery` before and after the validation, and the order is
        `delivered` only when the carrier delivered it.
        """
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=1)
        order.action_confirm()
        picking = order.picking_ids
        self.assertEqual(order.stage, "to_be_delivery")
        picking.write({"delivery_state": "pre_advice"})
        self.assertEqual(order.stage, "pre_advice")
        picking.write({"delivery_state": "in_transit"})
        self.assertEqual(order.stage, "in_delivery")
        self._deliver(picking)
        self.assertEqual(picking.state, "done")
        self.assertEqual(order.stage, "in_delivery")
        picking.write({"delivery_state": "in_warehouse"})
        self.assertEqual(order.stage, "in_delivery")
        picking.write({"delivery_state": "delivered"})
        self.assertEqual(order.stage, "delivered")

    def test_picking_delivery_state_storable_validated_with_awb(self):
        """Validated transfer with an AWB not yet picked up by the carrier: not delivered yet."""
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=1)
        order.action_confirm()
        picking = order.picking_ids
        self._deliver(picking)
        self.assertEqual(order.stage, "delivered")
        picking.write({"delivery_state": "pre_advice"})
        self.assertEqual(order.stage, "pre_advice")

    def test_picking_delivery_state_does_not_hide_waiting(self):
        """A carrier status does not override a stage that is not about delivery."""
        order = self._create_order(self.storable, qty=5)
        order.action_confirm()
        self.assertEqual(order.stage, "waiting")
        order.picking_ids.write({"delivery_state": "pre_advice"})
        self.assertEqual(order.stage, "waiting")

    def test_picking_delivery_state_canceled_order(self):
        order, picking = self._confirmed_goods_order()
        picking.write({"delivery_state": "in_transit"})
        order._action_cancel()
        self.assertEqual(order.stage, "canceled")

    def test_picking_write_without_sale(self):
        picking_type = self.warehouse.out_type_id
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )
        for delivery_state in ("in_transit", "delivered", "pre_advice"):
            picking.write({"delivery_state": delivery_state})
            self.assertEqual(picking.delivery_state, delivery_state)
        picking.write({"note": "no delivery state"})

    def test_picking_delivery_state_old_transfer_ignored(self):
        """A transfer no longer tracked keeps the stock stage, not a stale carrier status."""
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=1)
        order.action_confirm()
        picking = order.picking_ids
        self._deliver(picking)
        picking.write({"delivery_state": "in_transit"})
        self.assertEqual(order.stage, "in_delivery")
        picking.date_done = fields.Datetime.now() - timedelta(days=31)
        order._compute_stage()
        self.assertEqual(order.stage, "delivered")

    # ------------------------------------------------------------------
    # detailed stage off (default): stage of the stock moves
    # ------------------------------------------------------------------
    def test_default_website_sent_in_process(self):
        self._set_detailed_stage(False)
        order = self._create_order(self.storable, website_id=self.website.id)
        order.action_quotation_sent()
        self.assertEqual(order.stage, "in_process")

    def test_default_storable_delivered_at_validation(self):
        """The carrier status does not change the stage of storable products."""
        self._set_detailed_stage(False)
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=1)
        order.action_confirm()
        picking = order.picking_ids
        picking.write({"delivery_state": "pre_advice"})
        self.assertEqual(order.stage, "to_be_delivery")
        self._deliver(picking)
        picking.write({"delivery_state": "in_transit"})
        self.assertEqual(order.stage, "delivered")
        picking.write({"delivery_state": "delivered"})
        self.assertEqual(order.stage, "delivered")

    # ------------------------------------------------------------------
    # sale.report
    # ------------------------------------------------------------------
    def test_sale_report_stage_pre_advice(self):
        order, picking = self._confirmed_goods_order()
        picking.write({"delivery_state": "pre_advice"})
        self.env.flush_all()
        groups = self.env["sale.report"]._read_group(
            [("order_reference", "=", f"sale.order,{order.id}")], ["stage"], ["__count"]
        )
        self.assertEqual([stage for stage, _count in groups], ["pre_advice"])

    def test_sale_report_stage(self):
        self._put_in_stock(self.storable, 10)
        order = self._create_order(self.storable, qty=1)
        order.action_confirm()
        self.env.flush_all()
        report = self.env["sale.report"].search([("order_reference", "=", f"sale.order,{order.id}")])
        self.assertTrue(report)
        self.assertEqual(set(report.mapped("stage")), {"to_be_delivery"})
        groups = self.env["sale.report"]._read_group([("partner_id", "=", self.partner.id)], ["stage"], ["__count"])
        self.assertIn("to_be_delivery", [stage for stage, _count in groups])
