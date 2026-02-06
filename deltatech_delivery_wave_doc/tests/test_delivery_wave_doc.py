from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDeliveryWaveDoc(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Supplier",
                "supplier_rank": 1,
                "company_id": self.company.id,
            }
        )
        # Products
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.product_a = self.env["product.product"].create(
            {
                "name": "Prod A",
                "default_code": "PROD_A",
                "type": "product",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Prod B",
                "default_code": "PROD_B",
                "type": "product",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
            }
        )

        # Operation type: Receipts
        self.picking_type_in = self.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", self.company.id)], limit=1
        )
        if not self.picking_type_in:
            # Fall back: any incoming type in company
            self.picking_type_in = self.env["stock.picking.type"].search([("code", "=", "incoming")], limit=1)

        # Create a PO with two lines and confirm -> creates incoming picking with moves
        self.po = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "name": "A",
                            "product_qty": 5,
                            "product_uom": self.uom_unit.id,
                            "price_unit": 10,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_b.id,
                            "name": "B",
                            "product_qty": 3,
                            "product_uom": self.uom_unit.id,
                            "price_unit": 20,
                        },
                    ),
                ],
            }
        )
        self.po.button_confirm()

        # Find the created incoming picking
        self.picking = self.env["stock.picking"].search(
            [
                ("origin", "=", self.po.name),
                ("picking_type_id.code", "=", "incoming"),
            ],
            limit=1,
        )
        self.assertTrue(self.picking, "Incoming picking should have been created after PO confirmation")

    def test_generate_wave_single(self):
        Doc = self.env["delivery.vendor.document"]
        doc = Doc.create(
            {
                "partner_id": self.partner.id,
                "document_no": "DN-001",
                "company_id": self.company.id,
                "picking_type_id": self.picking_type_in.id,
                "line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "quantity": 2, "product_uom": self.uom_unit.id}),
                    (0, 0, {"product_id": self.product_b.id, "quantity": 1, "product_uom": self.uom_unit.id}),
                ],
            }
        )

        # Action should create a single wave and set wave_id
        action = doc.action_generate_wave()
        self.assertTrue(action, "Action should return an act_window")
        self.assertTrue(doc.wave_id, "A wave should be created and linked on the document")
        self.assertEqual(doc.state, "processed")

        # The wave should contain our picking in draft/in_progress state
        batch = doc.wave_id
        self.assertEqual(batch.picking_type_id.code, "incoming")
        self.assertIn(self.picking, batch.picking_ids, "The PO receipt picking should be part of the wave")

    def test_import_wizard_adds_lines(self):
        # Prepare a small CSV in-memory
        content = """product,quantity,uom,price_unit\nPROD_A,1,Unit(s),9.5\nPROD_B,2,Unit(s),19\n"""
        file_b64 = self.env["ir.binary"]._encode_bytes(content.encode("utf-8"))

        doc = self.env["delivery.vendor.document"].create(
            {
                "partner_id": self.partner.id,
                "document_no": "DN-CSV",
                "company_id": self.company.id,
                "picking_type_id": self.picking_type_in.id,
            }
        )

        wiz = (
            self.env["delivery.vendor.document.import.wizard"]
            .with_context(active_id=doc.id)
            .create(
                {
                    "file": file_b64,
                    "filename": "lines.csv",
                    "file_type": "csv",
                    "product_match_by": "default_code",
                }
            )
        )
        wiz.action_import()

        self.assertEqual(len(doc.line_ids), 2, "Two lines should be imported from CSV")
        qtys = {l.product_id.default_code: l.quantity for l in doc.line_ids}
        self.assertEqual(qtys.get("PROD_A"), 1.0)
        self.assertEqual(qtys.get("PROD_B"), 2.0)
