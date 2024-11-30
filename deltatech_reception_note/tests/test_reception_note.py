from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestPurchaseOrderReceptionType(TransactionCase):
    def setUp(self):
        super().setUp()
        self.PurchaseOrder = self.env["purchase.order"]
        self.PurchaseOrderLine = self.env["purchase.order.line"]
        self.ReceptionNoteCreate = self.env["reception.note.create"]
        self.Product = self.env["product.product"]
        self.Partner = self.env.ref("base.res_partner_1")
        self.PickingType = self.env.ref("stock.picking_type_in")

        # Create a product
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "default_code": "TEST_PRODUCT",
                "is_storable": True,
            }
        )

    def test_action_rfq_send(self):
        # Create a purchase order with reception_type 'note'
        purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.Partner.id,
                "reception_type": "note",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_qty": 10,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        # Send RFQ and check the state
        purchase_order.action_rfq_send()
        self.assertEqual(purchase_order.state, "draft", "State should remain draft for reception_type note")

    def test_set_sent(self):
        # Create a purchase order
        purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.Partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_qty": 10,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        # Set order to sent
        purchase_order.set_sent()
        self.assertEqual(purchase_order.state, "sent", "State should be sent")
        self.assertIsNotNone(purchase_order.date_sent, "Date sent should be set")

    def test_button_confirm_rfq_only(self):
        # Create a purchase order with reception_type 'rfq_only'
        purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.Partner.id,
                "reception_type": "rfq_only",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_qty": 10,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        # Attempt to confirm order
        with self.assertRaises(UserError):
            purchase_order.button_confirm()

    def test_reduce_from_rfq(self):
        # Create an RFQ purchase order
        rfq_order = self.PurchaseOrder.create(
            {
                "partner_id": self.Partner.id,
                "reception_type": "rfq_only",
                "state": "sent",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_qty": 10,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        # Create a reception note purchase order
        reception_order = self.PurchaseOrder.create(
            {
                "partner_id": self.Partner.id,
                "reception_type": "note",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_qty": 5,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        # Confirm the reception order
        reception_order.button_confirm()

        # Check if quantities are reduced in RFQ
        rfq_line = rfq_order.order_line.filtered(lambda li, product_id=self.product_id: li.product_id == product_id)
        self.assertEqual(rfq_line.product_qty, 5, "RFQ quantity should be reduced to 5")

    def test_do_create_reception_note(self):
        # Create a normal purchase order
        purchase_order = self.PurchaseOrder.create(
            {
                "partner_id": self.Partner.id,
                "reception_type": "normal",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_qty": 10,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        # Create a reception note from the wizard
        wizard = self.ReceptionNoteCreate.create({})
        wizard.with_context(active_ids=purchase_order.ids).do_create_reception_note()
