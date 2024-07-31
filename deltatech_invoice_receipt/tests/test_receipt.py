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
                "type": "product",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
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

        # Create and confirm a related purchase order
        purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.partner.id,
                "date_order": "2024-07-30",
                "from_invoice_id": invoice.id,
            }
        )

        self.PurchaseOrderLine.create(
            {
                "order_id": purchase_order.id,
                "product_id": self.product.id,
                "product_qty": 5,
                "product_uom": self.uom_unit.id,
                "price_unit": 100,
                "name": "Test Product",
            }
        )

        purchase_order.button_confirm()

        # Attempt to post the invoice
        invoice.action_post()

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

    def test_receipt_to_stock(self):
        # Create a purchase order and confirm it
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
                "product_qty": 5,
                "product_uom": self.uom_unit.id,
                "price_unit": 100,
                "name": "Test Product",
            }
        )

        purchase_order.button_confirm()

        # Assign and validate the picking
        purchase_order.receipt_to_stock()

        # Verify the stock picking is done
        self.StockPicking.search([("origin", "=", purchase_order.name)])


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
                "type": "product",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
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
                "product_uom": self.uom_unit.id,
                "price_unit": 100,
                "name": "Test Product",
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
