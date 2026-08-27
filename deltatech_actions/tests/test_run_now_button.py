# © 2026 Deltatech
# See README.rst file on addons root folder for license details

import base64
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRunNowButton(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env["ir.config_parameter"].sudo()
        cls.partner = cls.env["res.partner"].create({"name": "Run Now Customer"})
        cls.move = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": cls.env.cr.now(),
            }
        )

    def _create_old_pdf(self, name="RUNNOW_0001.pdf", days_ago=100):
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "account.move",
                "res_id": self.move.id,
                "type": "binary",
                "datas": base64.b64encode(b"pdf"),
                "mimetype": "application/pdf",
            }
        )
        past = datetime.utcnow() - timedelta(days=days_ago)
        self.env.cr.execute("UPDATE ir_attachment SET create_date = %s WHERE id = %s", (past, att.id))
        return att

    def _settings(self, dry_run):
        return self.env["res.config.settings"].create(
            {
                "dt_actions_invoice_pdf_dry_run": dry_run,
                "dt_actions_invoice_pdf_pattern": "RUNNOW_%",
                "dt_actions_invoice_pdf_max_date_days": 1,
                "dt_actions_invoice_pdf_limit": 100,
            }
        )

    def test_run_now_in_dry_run_reports_without_deleting(self):
        att = self._create_old_pdf()
        action = self._settings(dry_run=True).action_dt_actions_run_invoice_pdf()

        self.assertEqual(action["tag"], "display_notification")
        self.assertIn("would be deleted", action["params"]["message"])
        self.assertTrue(att.exists(), "dry run must not delete anything")

    def test_run_now_without_dry_run_deletes(self):
        att = self._create_old_pdf()
        action = self._settings(dry_run=False).action_dt_actions_run_invoice_pdf()

        self.assertEqual(action["params"]["type"], "success")
        self.assertIn("deleted", action["params"]["message"])
        self.assertFalse(att.exists())

    def test_xml_cleanup_counts_in_dry_run(self):
        """The XML cleanup used to report 0 in dry run, whatever it had found."""
        for _i in range(12):
            self.env["ir.attachment"].create(
                {
                    "name": "duplicate.xml",
                    "res_model": "account.move",
                    "res_id": self.move.id,
                    "type": "binary",
                    "datas": base64.b64encode(b"<xml/>"),
                    "mimetype": "application/xml",
                }
            )
        result = self.env["account.move"].cron_clean_xml_attachments(
            limit=10, duplicates=10, max_attachments_to_delete=50, dry_run=True
        )
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["count"], 12)
