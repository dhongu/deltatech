from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestPurchaseOrderReceptionType(TransactionCase):
    def setUp(self):
        super().setUp()
        self.PurchaseOrder = self.env["purchase.order"]
        self.PurchaseOrderLine = self.env["purchase.order.line"]
        self.ReceptionNoteCreate = self.env["reception.note.create"]
        self.Product = self.env["product.product"]
        self.Partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.PickingType = self.env["stock.picking.type"].search([("code", "=", "incoming")], limit=1)

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
                            "uom_id": self.product.uom_id.id,
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
                            "uom_id": self.product.uom_id.id,
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
                            "uom_id": self.product.uom_id.id,
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
                            "uom_id": self.product.uom_id.id,
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
                            "uom_id": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        # Confirm the reception order
        reception_order.button_confirm()

        # Check if quantities are reduced in RFQ
        rfq_line = rfq_order.order_line.filtered(lambda li, product_id=self.product: li.product_id == product_id)
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
                            "uom_id": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        # Create a reception note from the wizard
        wizard = self.ReceptionNoteCreate.create({})
        wizard.with_context(active_ids=purchase_order.ids).do_create_reception_note()

    def _uom_pack(self):
        return self.env["uom.uom"].create(
            {
                "name": "Pack of 12",
                "relative_factor": 12,
                "relative_uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

    def _order(self, reception_type, qty, uom, state="draft"):
        return self.PurchaseOrder.create(
            {
                "partner_id": self.Partner.id,
                "reception_type": reception_type,
                "state": state,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_qty": qty,
                            "uom_id": uom.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

    def test_reduce_from_rfq_note_in_dozens(self):
        """RECEPTION-001: o nota de 1 duzina consuma 12 bucati din RFQ, nu una."""
        rfq_order = self._order("rfq_only", 12, self.product.uom_id, state="sent")
        reception_order = self._order("note", 1, self.env.ref("uom.product_uom_dozen"))
        reception_order.button_confirm()
        self.assertEqual(rfq_order.order_line.product_qty, 0)
        self.assertTrue(rfq_order.is_empty)

    def test_reduce_from_rfq_rfq_in_packs(self):
        """RECEPTION-001: 6 bucati receptionate dintr-un RFQ de 2 baxuri lasa 1,5 baxuri."""
        pack = self._uom_pack()
        rfq_order = self._order("rfq_only", 2, pack, state="sent")
        reception_order = self._order("note", 6, self.product.uom_id)
        reception_order.button_confirm()
        self.assertEqual(rfq_order.order_line.uom_id, pack)
        self.assertAlmostEqual(rfq_order.order_line.product_qty, 1.5)
        self.assertFalse(rfq_order.is_empty)

    def test_reduce_from_rfq_missing_quantity_in_note_unit(self):
        """RECEPTION-001: cantitatea lipsa e raportata in unitatea notei."""
        self._order("rfq_only", 6, self.product.uom_id, state="sent")
        reception_order = self._order("note", 1, self.env.ref("uom.product_uom_dozen"))
        with self.assertRaisesRegex(UserError, "quantity 0.5 of"):
            reception_order.button_confirm()

    def test_reconfirm_does_not_consume_rfq_again(self):
        """RECEPTION-003: o nota confirmata a doua oara nu mai scade din RFQ."""
        rfq_order = self._order("rfq_only", 10, self.product.uom_id, state="sent")
        reception_order = self._order("note", 5, self.product.uom_id)
        reception_order.button_confirm()
        self.assertEqual(reception_order.state, "purchase")
        reception_order.button_confirm()
        self.assertEqual(rfq_order.order_line.product_qty, 5)

    def test_confirm_with_an_already_confirmed_note(self):
        """RECEPTION-003: intr-o selectie mixta scade doar nota care se confirma acum."""
        rfq_order = self._order("rfq_only", 10, self.product.uom_id, state="sent")
        confirmed = self._order("note", 3, self.product.uom_id)
        confirmed.button_confirm()
        new_note = self._order("note", 2, self.product.uom_id)
        (confirmed | new_note).button_confirm()
        self.assertEqual(new_note.state, "purchase")
        self.assertEqual(rfq_order.order_line.product_qty, 5)
