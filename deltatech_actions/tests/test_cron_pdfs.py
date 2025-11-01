# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCronGeneratedPDFs(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Minimal partner for sale order
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
            }
        )
        # Create an empty sale order to attach files to
        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
            }
        )

    def _create_attachment_for_so(self, name="SO_TEST.pdf", days_ago=10, mimetype="application/pdf"):
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "sale.order",
                "res_id": self.so.id,
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

    def test_sale_order_cron_dry_run_and_delete(self):
        # Create two attachments: one matching the pattern and one not
        att_match = self._create_attachment_for_so(name="SO_0001.pdf", days_ago=30)
        att_other = self._create_attachment_for_so(name="OTHER_0001.pdf", days_ago=30)

        # Dry run with pattern 'SO_%' should only return the matching one
        rows = self.env["sale.order"].cron_clean_generated_pdfs(
            limit=100, pattern="SO_%", max_date_days=1, dry_run=True
        )
        ids = {r[0] for r in rows}
        self.assertIn(att_match.id, ids)
        self.assertNotIn(att_other.id, ids)

        # Real delete should remove only the matching one
        self.env["sale.order"].cron_clean_generated_pdfs(limit=100, pattern="SO_%", max_date_days=1, dry_run=False)
        self.assertFalse(att_match.exists())
        self.assertTrue(att_other.exists())

        # With empty pattern (defaults to '%%'), the remaining one is selected and deleted
        rows_all = self.env["sale.order"].cron_clean_generated_pdfs(
            limit=100, pattern="", max_date_days=1, dry_run=True
        )
        ids_all = {r[0] for r in rows_all}
        self.assertIn(att_other.id, ids_all)

        self.env["sale.order"].cron_clean_generated_pdfs(limit=100, pattern="", max_date_days=1, dry_run=False)
        self.assertFalse(att_other.exists())
