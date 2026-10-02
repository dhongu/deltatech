# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from io import BytesIO
from unittest.mock import patch

import openpyxl

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

DUMMY_PDF = b"%PDF-1.4\n%dummy"
REPORT_PATH = "odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf"


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
                "uom_id": cls.product_1.uom_id.id,
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
                "uom_id": cls.product_2.uom_id.id,
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

    def _compose(self, pos):
        with patch(REPORT_PATH, return_value=(DUMMY_PDF, "pdf")):
            return pos.action_compose_batch_email()

    def test_attachment_content_raw_bytes(self):
        action = self._compose(self.po1 | self.po2)
        atts = self.env["ir.attachment"].browse(action["context"]["default_attachment_ids"][0][2])
        pdfs = atts.filtered(lambda a: a.mimetype == "application/pdf")
        self.assertEqual(len(pdfs), 2)
        for pdf in pdfs:
            # stored as raw bytes, not base64-encoded twice
            self.assertEqual(pdf.raw.content, DUMMY_PDF)
        xlsx = atts.filtered(lambda a: a.name.endswith(".xlsx"))
        self.assertEqual(len(xlsx), 1)
        self.assertEqual(xlsx.mimetype, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        wiz = self.env["purchase.send.xlsx.wizard"].browse(action["context"]["default_res_ids"])
        self.assertEqual(set(atts.mapped("res_model")), {wiz._name})
        self.assertEqual(set(atts.mapped("res_id")), {wiz.id})
        self.assertEqual(wiz.purchase_ids, self.po1 | self.po2)

    def test_xlsx_content(self):
        self.po1.order_line.name = "Extra description"
        data = (self.po1 | self.po2)._build_xlsx()
        sheet = openpyxl.load_workbook(BytesIO(data)).active
        rows = list(sheet.iter_rows(values_only=True))
        self.assertEqual(rows[0], ("Order", "Product Code", "Product Description", "Quantity", "Price"))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1][0], self.po1.name)
        self.assertEqual(rows[1][1], "W-A")
        # product name is kept in the description column, plus the extra description
        self.assertIn("Widget A", rows[1][2])
        self.assertIn("Extra description", rows[1][2])
        self.assertEqual(rows[1][3:], (3, 10))
        self.assertEqual(rows[2][0], self.po2.name)
        self.assertIn("Widget B", rows[2][2])
        self.assertEqual(rows[2][3:], (5, 20.5))

    def test_marks_rfq_as_sent(self):
        pos = self.po1 | self.po2
        self.assertEqual(set(pos.mapped("state")), {"draft"})
        self._compose(pos)
        self.assertEqual(set(pos.mapped("state")), {"sent"})
        for po in pos:
            self.assertIn("batch compose", po.message_ids[0].body)

    def test_multiple_vendors_refused(self):
        other_vendor = self.env["res.partner"].create({"name": "Other Vendor", "email": "other@example.com"})
        po3 = self.env["purchase.order"].create({"partner_id": other_vendor.id})
        with self.assertRaises(UserError):
            self._compose(self.po1 | po3)

    def test_vendor_without_email_refused(self):
        self.partner_vendor.email = False
        with self.assertRaises(UserError):
            self._compose(self.po1)

    def test_send_through_composer(self):
        pos = self.po1 | self.po2
        action = self._compose(pos)
        composer = self.env["mail.compose.message"].with_context(**action["context"]).create({})
        self.assertEqual(composer.template_id, self.env.ref("deltatech_purchase_mail.mail_template_purchase_send_xlsx"))
        self.assertEqual(composer.subject, "Purchase Orders")
        # the template body is rendered with t-out (t-esc is ignored server-side in 20.0)
        self.assertIn(self.po1.name, composer.body)
        self.assertIn(self.po2.name, composer.body)
        self.assertIn(self.partner_vendor, composer.partner_ids)
        self.assertEqual(len(composer.attachment_ids), 3)
        composer.action_send_mail()
        message = self.env["mail.message"].search(
            [("model", "=", "purchase.send.xlsx.wizard"), ("res_id", "in", action["context"]["default_res_ids"])]
        )
        self.assertEqual(len(message), 1)
        self.assertIn(self.partner_vendor, message.partner_ids)
        self.assertEqual(len(message.attachment_ids), 3)
