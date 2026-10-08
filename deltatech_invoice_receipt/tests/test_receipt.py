from odoo.tests.common import TransactionCase


class TestAccountInvoice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.AccountMove = self.env["account.move"]
        self.PurchaseOrder = self.env["purchase.order"]
        self.StockPicking = self.env["stock.picking"]
        self.Partner = self.env["res.partner"]
        self.Product = self.env["product.product"]
        self.PurchaseOrderLine = self.env["purchase.order.line"]
        self.InvoiceLine = self.env["account.move.line"]
        self.UoM = self.env["uom.uom"]
        self.Tax = self.env["account.tax"]

        # Create test records
        self.partner = self.Partner.create({"name": "Test Partner"})
        self.uom_unit = self.UoM.search([("name", "=", "Units")], limit=1)
        self.tax = self.Tax.create({"name": "Test Tax", "amount": 15, "type_tax_use": "purchase"})
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "is_storable": True,
                "uom_id": self.uom_unit.id,
            }
        )

    def test_action_post(self):
        # Create a draft invoice
        invoice = self.AccountMove.create(
            {
                "partner_id": self.partner.id,
                "move_type": "in_invoice",
                "invoice_date": "2024-07-31",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 5,
                            "price_unit": 100,
                            "tax_ids": [(6, 0, [self.tax.id])],
                            "product_uom_id": self.uom_unit.id,
                            "name": "Test Product",
                        },
                    )
                ],
            }
        )

        # First post: the purchase order is generated from the invoice and must be confirmed
        action = invoice.action_post()
        self.assertEqual(action.get("tag"), "display_notification")
        self.assertEqual(invoice.state, "draft")
        purchase_order = self.PurchaseOrder.search([("from_invoice_id", "=", invoice.id)])
        self.assertEqual(len(purchase_order), 1)
        purchase_order.button_confirm()

        # Second post: the invoice is posted and the ordered quantity is received in stock
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(purchase_order.picking_ids.mapped("state"), ["done"])
        self.assertEqual(purchase_order.order_line.qty_received, 5)
        self.assertEqual(self.product.qty_available, 5)

    def test_add_to_purchase(self):
        # Create a draft invoice
        invoice = self.AccountMove.create(
            {
                "partner_id": self.partner.id,
                "move_type": "in_invoice",
                "invoice_date": "2024-07-31",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 5,
                            "price_unit": 100,
                            "tax_ids": [(6, 0, [self.tax.id])],
                            "product_uom_id": self.uom_unit.id,
                            "name": "Test Product",
                        },
                    )
                ],
            }
        )

        # Add to purchase order
        invoice.add_to_purchase()

        # Verify the creation of a purchase order
        purchase_order = self.PurchaseOrder.search([("from_invoice_id", "=", invoice.id)])
        self.assertTrue(purchase_order, "Purchase order should be created from the invoice.")

    def _create_confirmed_purchase(self, qty=5):
        purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.partner.id,
                "date_order": "2024-07-30",
            }
        )
        self.PurchaseOrderLine.create(
            {
                "order_id": purchase_order.id,
                "product_id": self.product.id,
                "product_qty": qty,
                "uom_id": self.uom_unit.id,
                "price_unit": 100,
                "name": "Test Product",
            }
        )
        purchase_order.button_confirm()
        return purchase_order

    def _assert_received(self, purchase_order, qty, location=None):
        receipts = purchase_order.picking_ids.filtered(lambda p: p.picking_type_id.code == "incoming")
        self.assertEqual(receipts.mapped("state"), ["done"], "The receipt should be validated, without backorder.")
        self.assertEqual(receipts.move_ids.filtered(lambda m: m.state == "done").mapped("quantity"), [qty])
        self.assertEqual(purchase_order.order_line.qty_received, qty)
        if location:
            self.assertEqual(self.product.with_context(location=location.id).qty_available, qty)

    def test_receipt_to_stock(self):
        # In O19 the supplier receipt is reserved in full at confirmation (quantity == demand)
        purchase_order = self._create_confirmed_purchase()
        receipt = purchase_order.picking_ids
        self.assertEqual(receipt.move_ids.quantity, 5)

        purchase_order.receipt_to_stock()

        self._assert_received(purchase_order, 5)
        self.assertEqual(self.product.qty_available, 5)

    def test_receipt_to_stock_partial_quantity(self):
        # A partially entered quantity is completed up to the ordered (invoiced) quantity
        purchase_order = self._create_confirmed_purchase()
        purchase_order.picking_ids.move_ids.quantity = 2

        purchase_order.receipt_to_stock()

        self._assert_received(purchase_order, 5)
        self.assertEqual(self.product.qty_available, 5)

    def test_receipt_to_stock_zero_quantity(self):
        # No quantity on the move: the ordered quantity is received
        purchase_order = self._create_confirmed_purchase()
        purchase_order.picking_ids.move_ids.quantity = 0

        purchase_order.receipt_to_stock()

        self._assert_received(purchase_order, 5)

    def test_receipt_to_stock_two_steps(self):
        # Receipt in 2 steps: the receipt move is chained to the internal move (move_dest_ids)
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        warehouse.reception_steps = "two_steps"
        purchase_order = self._create_confirmed_purchase()

        purchase_order.receipt_to_stock()

        self._assert_received(purchase_order, 5, location=warehouse.wh_input_stock_loc_id)


class TestStockPicking(TransactionCase):
    def setUp(self):
        super().setUp()
        self.StockPicking = self.env["stock.picking"]
        self.PurchaseOrder = self.env["purchase.order"]
        self.PurchaseOrderLine = self.env["purchase.order.line"]
        self.Partner = self.env["res.partner"]
        self.Product = self.env["product.product"]
        self.UoM = self.env["uom.uom"]
        self.Tax = self.env["account.tax"]

        # Create test records
        self.partner = self.Partner.create({"name": "Test Partner"})
        self.uom_unit = self.UoM.search([("name", "=", "Units")], limit=1)
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "is_storable": True,
                "uom_id": self.uom_unit.id,
            }
        )

    def test_create_return_picking(self):
        # Create a purchase order with a return picking
        purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.partner.id,
                "date_order": "2024-07-30",
            }
        )

        self.PurchaseOrderLine.create(
            {
                "order_id": purchase_order.id,
                "product_id": self.product.id,
                "product_qty": -5,
                "uom_id": self.uom_unit.id,
                "price_unit": 100,
            }
        )

        purchase_order._create_picking()

        # Verify the creation of a return picking
        picking = self.StockPicking.search([("origin", "=", purchase_order.name)])
        self.assertTrue(picking, "Return picking should be created from the purchase order.")
        self.assertEqual(
            picking.picking_type_id,
            purchase_order.picking_type_id.return_picking_type_id,
            "Picking type should be return picking type.",
        )

    def _return_order(self, qty, uom=None, partner=None):
        purchase_order = self.PurchaseOrder.create(
            {"partner_id": (partner or self.partner).id, "date_order": "2024-07-30"}
        )
        self.PurchaseOrderLine.create(
            {
                "order_id": purchase_order.id,
                "product_id": self.product.id,
                "product_qty": qty,
                "uom_id": (uom or self.uom_unit).id,
                "price_unit": 100,
            }
        )
        return purchase_order

    def _return_moves(self, purchase_order):
        return self.StockPicking.search([("origin", "=", purchase_order.name)]).move_ids

    def test_return_moves_count_existing_returns(self):
        """The quantity already returned is subtracted from the requested return"""
        purchase_order = self._return_order(-5)
        purchase_order._create_picking()
        self.assertEqual(self._return_moves(purchase_order).product_uom_qty, 5)

        line = purchase_order.order_line
        line.product_qty = -7
        picking = self._return_moves(purchase_order).picking_id
        vals = line.with_context(return_picking=True)._prepare_stock_moves(picking)
        # 5 already returned, only the 2 extra units are requested
        self.assertEqual([v["product_uom_qty"] for v in vals], [2])

        line.product_qty = -5
        self.assertEqual(line.with_context(return_picking=True)._prepare_stock_moves(picking), [])

    def test_return_keeps_purchase_unit(self):
        """With propagated units, a return of 2 dozens moves 24 units"""
        self.env["ir.config_parameter"].sudo().set_bool("stock.propagate_uom", True)
        uom_dozen = self.env.ref("uom.product_uom_dozen")
        purchase_order = self._return_order(-2, uom=uom_dozen)
        purchase_order._create_picking()
        move = self._return_moves(purchase_order)
        self.assertEqual(move.uom_id, uom_dozen)
        self.assertEqual(move.product_uom_qty, 2)
        self.assertEqual(move.product_qty, 24)

    def test_return_converted_to_product_unit(self):
        """Without propagated units the return is expressed in the product unit"""
        self.env["ir.config_parameter"].sudo().set_bool("stock.propagate_uom", False)
        purchase_order = self._return_order(-2, uom=self.env.ref("uom.product_uom_dozen"))
        purchase_order._create_picking()
        move = self._return_moves(purchase_order)
        self.assertEqual(move.uom_id, self.uom_unit)
        self.assertEqual(move.product_uom_qty, 24)

    def test_create_return_pickings_for_several_orders(self):
        """Several orders with returns are processed together"""
        other_partner = self.Partner.create({"name": "Other Return Partner"})
        orders = self._return_order(-3) | self._return_order(-4, partner=other_partner)
        orders._create_picking()
        for order, partner, qty in zip(orders, [self.partner, other_partner], [3, 4], strict=True):
            picking = self.StockPicking.search([("origin", "=", order.name)])
            self.assertEqual(len(picking), 1)
            self.assertEqual(picking.partner_id, partner)
            self.assertEqual(picking.location_dest_id, partner.property_stock_supplier)
            self.assertEqual(picking.move_ids.product_uom_qty, qty)
