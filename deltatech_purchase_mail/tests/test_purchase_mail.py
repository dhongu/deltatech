# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDeltatechPurchaseMail(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Company and basic partners/products
        cls.partner_vendor = cls.env["res.partner"].create(
            {
                "name": "Acme Supplies",
                "email": "buy@acme.example.com",
                "supplier_rank": 1,
            }
        )

        cls.product_1 = cls.env["product.product"].create(
            {"name": "Widget A", "default_code": "W-A", "is_storable": True}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Widget B", "default_code": "W-B", "is_storable": True}
        )

        # Create two Purchase Orders for the same vendor
        cls.po1 = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner_vendor.id,
                "date_order": fields.Datetime.now(),
            }
        )
        cls.env["purchase.order.line"].create(
            {
                "order_id": cls.po1.id,
                "product_id": cls.product_1.id,
                "name": cls.product_1.display_name,
                "product_qty": 3,
                "price_unit": 10.0,
                "product_uom": cls.product_1.uom_id.id,
                "date_planned": fields.Datetime.now(),
            }
        )

        cls.po2 = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner_vendor.id,
                "date_order": fields.Datetime.now(),
            }
        )
        cls.env["purchase.order.line"].create(
            {
                "order_id": cls.po2.id,
                "product_id": cls.product_2.id,
                "name": cls.product_2.display_name,
                "product_qty": 5,
                "price_unit": 20.5,
                "product_uom": cls.product_2.uom_id.id,
                "date_planned": fields.Datetime.now(),
            }
        )

    def test_compose_action_context_and_attachments(self):
        pos = self.po1 | self.po2
        report_path = "odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf"
        with patch(report_path, return_value=(b"%PDF-1.4\n%dummy", "pdf")) as mocked_pdf:
            action = pos.action_compose_batch_email()

        # Basic action checks
        self.assertEqual(action.get("res_model"), "mail.compose.message")
        self.assertEqual(action.get("target"), "new")
        ctx = action.get("context") or {}
        self.assertEqual(ctx.get("default_model"), "purchase.send.xlsx.wizard")
        res_ids = ctx.get("default_res_ids")
        self.assertIsInstance(res_ids, list)
        self.assertEqual(len(res_ids), 1)
        self.assertIsInstance(res_ids[0], int)
        # mark RFQ as sent flag present in context
        self.assertTrue(ctx.get("mark_rfq_as_sent"))
        # Template should be set by default
        self.assertTrue(ctx.get("default_template_id"))
        # Email to should be vendor email since both POs share the same vendor
        self.assertEqual(ctx.get("default_email_to"), self.partner_vendor.email)
        # Attachments must include 1 xlsx + 2 pdfs
        attach_cmd = ctx.get("default_attachment_ids")
        self.assertIsInstance(attach_cmd, list)
        self.assertEqual(attach_cmd[0][0], 6)
        attach_ids = attach_cmd[0][2]
        self.assertGreaterEqual(len(attach_ids), 3)

        # Inspect attachments
        atts = self.env["ir.attachment"].browse(attach_ids)
        names = atts.mapped("name")
        self.assertTrue(any(n.endswith(".xlsx") for n in names))
        self.assertTrue(any(self.po1.name.replace("/", "-") in n and n.endswith(".pdf") for n in names))
        self.assertTrue(any(self.po2.name.replace("/", "-") in n and n.endswith(".pdf") for n in names))
        # Ensure PDF render called per PO
        self.assertGreaterEqual(mocked_pdf.call_count, 2)
