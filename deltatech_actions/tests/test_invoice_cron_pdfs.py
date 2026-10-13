# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInvoiceCronGeneratedPDFs(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Minimal partner and customer invoice to attach files to
        cls.partner = cls.env["res.partner"].create({"name": "INV Customer"})
        cls.move = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": cls.env.cr.now(),
            }
        )

    def _create_attachment_for_invoice(self, name="INV_TEST.pdf", days_ago=10, mimetype="application/pdf"):
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "account.move",
                "res_id": self.move.id,
                "type": "binary",
                "datas": base64.b64encode(b"test pdf content"),
                "mimetype": mimetype,
            }
        )
        # Force create_date into the past so it matches the cron selection
        past_dt = datetime.utcnow() - timedelta(days=days_ago)
        self.env.cr.execute(
            "UPDATE ir_attachment SET create_date = %s WHERE id = %s",
            (past_dt, att.id),
        )
        return att

    def test_invoice_cron_dry_run_and_delete(self):
        # Create two attachments: one matching the pattern and one not
        att_match = self._create_attachment_for_invoice(name="INV_0001.pdf", days_ago=30)
        att_other = self._create_attachment_for_invoice(name="OTHER_0001.pdf", days_ago=30)

        # Dry run with pattern 'INV_%' should only return the matching one
        rows = self.env["account.move"].cron_clean_generated_pdfs(
            limit=100, pattern="INV_%", max_date_days=1, dry_run=True
        )
        ids = {r[0] for r in rows}
        self.assertIn(att_match.id, ids)
        self.assertNotIn(att_other.id, ids)

        # Real delete should remove only the matching one
        self.env["account.move"].cron_clean_generated_pdfs(limit=100, pattern="INV_%", max_date_days=1, dry_run=False)
        self.assertFalse(att_match.exists())
        self.assertTrue(att_other.exists())

        # With empty pattern (defaults to '%%'), the remaining one is selected and deleted
        rows_all = self.env["account.move"].cron_clean_generated_pdfs(
            limit=100, pattern="", max_date_days=1, dry_run=True
        )
        ids_all = {r[0] for r in rows_all}
        self.assertIn(att_other.id, ids_all)

        self.env["account.move"].cron_clean_generated_pdfs(limit=100, pattern="", max_date_days=1, dry_run=False)
        self.assertFalse(att_other.exists())

    def test_invoice_cron_catches_pdf_attached_via_mail_message(self):
        # This is how the PDF actually reaches ir_attachment when an invoice
        # is sent by email ("Send & Print"): attached to the outgoing
        # mail.message, not to the move itself.
        message = self.env["mail.message"].create(
            {
                "model": "account.move",
                "res_id": self.move.id,
                "message_type": "comment",
                "subject": "Invoice email",
            }
        )
        att = self.env["ir.attachment"].create(
            {
                "name": "INV_0002.pdf",
                "res_model": "mail.message",
                "res_id": message.id,
                "type": "binary",
                "datas": base64.b64encode(b"test pdf content"),
                "mimetype": "application/pdf",
            }
        )
        past_dt = datetime.utcnow() - timedelta(days=30)
        self.env.cr.execute("UPDATE ir_attachment SET create_date = %s WHERE id = %s", (past_dt, att.id))

        rows = self.env["account.move"].cron_clean_generated_pdfs(limit=100, max_date_days=1, dry_run=True)
        self.assertIn(att.id, {r[0] for r in rows})

        self.env["account.move"].cron_clean_generated_pdfs(limit=100, max_date_days=1, dry_run=False)
        self.assertFalse(att.exists())
