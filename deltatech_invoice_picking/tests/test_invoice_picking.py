from odoo import fields
from odoo.tests import common


class TestStockAccountCustom(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.Product = self.env["product.product"]
        self.Partner = self.env["res.partner"]
        self.PurchaseOrder = self.env["purchase.order"]
        self.SaleOrder = self.env["sale.order"]
        self.StockPicking = self.env["stock.picking"]
        self.AccountMove = self.env["account.move"]

        # Create sample data for testing
        self.partner = self.Partner.create({"name": "Test Partner"})
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "is_storable": True,
                "default_code": "PROD_TEST",
                "list_price": 100.0,
            }
        )

        # Create a Purchase Order
        self.purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.partner.id,
                "date_order": fields.Date.today(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_qty": 10.0,
                            "product_uom_id": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                            "date_planned": fields.Date.today(),
                        },
                    )
                ],
            }
        )

        # Confirm the Purchase Order
        self.purchase_order.button_confirm()

        # Create a Sale Order
        self.sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 10.0,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

        # Confirm the Sale Order
        self.sale_order.action_confirm()

        # Validate incoming picking
        self.picking_in = self.purchase_order.picking_ids[0]
        self.picking_in.move_line_ids[0].quantity = 10
        self.picking_in.button_validate()

        # Validate outgoing picking
        self.picking_out = self.sale_order.picking_ids[0]
        self.picking_out.move_line_ids[0].quantity = 10
        self.picking_out.button_validate()

    def test_action_create_supplier_invoice(self):
        self.picking_in.write({"supplier_invoice_number": "INV/2023/001"})
        self.picking_in.action_create_supplier_invoice()
        self.assertTrue(self.picking_in.account_move_id, "Supplier invoice was not created from picking")

    def test_action_create_invoice(self):
        self.picking_out.action_create_invoice()

    def test_search_invoiced(self):
        Batch = self.env["stock.picking.batch"]
        # lotul se formeaza inainte de validare: _sanity_check refuza livrarile done
        purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.partner.id,
                "date_order": fields.Date.today(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_qty": 5.0,
                            "product_uom_id": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                            "date_planned": fields.Date.today(),
                        },
                    )
                ],
            }
        )
        purchase_order.button_confirm()
        picking = purchase_order.picking_ids[0]
        batch = Batch.create({"picking_ids": [(6, 0, picking.ids)]})

        self.assertFalse(batch.invoiced)
        self.assertIn(batch, Batch.search([("invoiced", "=", False)]))
        self.assertNotIn(batch, Batch.search([("invoiced", "=", True)]))
        # operatorii inversi trebuie sa dea acelasi rezultat
        self.assertIn(batch, Batch.search([("invoiced", "!=", True)]))
        self.assertNotIn(batch, Batch.search([("invoiced", "!=", False)]))

        picking.move_line_ids[0].quantity = 5
        picking.button_validate()
        picking.write({"supplier_invoice_number": "INV/2023/002"})
        picking.action_create_supplier_invoice()
        self.assertTrue(picking.account_move_id)

        batch.invalidate_recordset(["invoiced"])
        self.assertTrue(batch.invoiced)
        self.assertIn(batch, Batch.search([("invoiced", "=", True)]))
        self.assertNotIn(batch, Batch.search([("invoiced", "=", False)]))

    def test_sale_invoice_creation(self):
        invoice = self.sale_order._create_invoices()
        self.assertTrue(invoice, "Invoice was not created for Sale Order")
        self.assertEqual(invoice.state, "draft", "Invoice state is not draft")
