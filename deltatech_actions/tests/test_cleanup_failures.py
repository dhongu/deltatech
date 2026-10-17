# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""ACTIONS-005 (#3362): when the deletion is refused, the cleanups used to log the
error and still report the selected records as deleted."""

import base64
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


def _refuse_unlink(self):
    raise UserError(self.env._("Deletion refused by another module"))


@tagged("post_install", "-at_install")
class TestCleanupFailures(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Refused Cleanup Customer"})
        cls.move = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": cls.env.cr.now(),
            }
        )
        cls.attachment_class = type(cls.env["ir.attachment"])

    def _create_old_pdf(self, name="REFUSED_0001.pdf", days_ago=100):
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

    def _settings(self):
        return self.env["res.config.settings"].create(
            {
                "dt_actions_invoice_pdf_dry_run": False,
                "dt_actions_invoice_pdf_pattern": "REFUSED_%",
                "dt_actions_invoice_pdf_max_date_days": 1,
                "dt_actions_invoice_pdf_limit": 100,
            }
        )

    def test_run_now_reports_refused_deletion(self):
        att = self._create_old_pdf()
        settings = self._settings()
        with patch.object(self.attachment_class, "unlink", _refuse_unlink):
            action = settings.action_dt_actions_run_invoice_pdf()

        params = action["params"]
        self.assertEqual(params["type"], "danger")
        self.assertNotIn("deleted.", params["message"])
        self.assertIn("Deletion refused by another module", params["message"])
        self.assertTrue(att.exists())
        # the settings shown on screen were still saved
        icp = self.env["ir.config_parameter"].sudo()
        self.assertEqual(icp.get_param("deltatech_actions.invoice_pdf_pattern"), "REFUSED_%")

    def test_pdf_cleanup_does_not_report_refused_rows(self):
        self._create_old_pdf()
        with (
            patch.object(self.attachment_class, "unlink", _refuse_unlink),
            self.assertRaises(UserError),
        ):
            self.env["account.move"].cron_clean_generated_pdfs(pattern="REFUSED_%", max_date_days=1, dry_run=False)

    def test_message_cleanup_does_not_report_refused_deletion(self):
        message = self.env["mail.message"].create(
            {"subject": "REFUSED_MSG", "body": "x", "model": "res.partner", "res_id": self.partner.id}
        )
        past = datetime.utcnow() - timedelta(days=30)
        self.env.cr.execute("UPDATE mail_message SET create_date = %s WHERE id = %s", (past, message.id))
        with (
            patch.object(type(self.env["mail.message"]), "unlink", _refuse_unlink),
            self.assertRaises(UserError),
        ):
            self.env["mail.message"].cron_clean_old_messages(
                pattern="REFUSED_%", max_date_days=1, dry_run=False, exclude_models=["business.%"]
            )

    def test_xml_cleanup_counts_only_deleted(self):
        for _i in range(12):
            self.env["ir.attachment"].create(
                {
                    "name": "refused.xml",
                    "res_model": "account.move",
                    "res_id": self.move.id,
                    "type": "binary",
                    "datas": base64.b64encode(b"<xml/>"),
                    "mimetype": "application/xml",
                }
            )
        with patch.object(self.attachment_class, "unlink", _refuse_unlink):
            result = self.env["account.move"].cron_clean_xml_attachments(
                limit=10, duplicates=10, max_attachments_to_delete=50, dry_run=False
            )
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["failed"], 11)
        message = self.env["res.config.settings"]._dt_actions_run_message(result)
        self.assertIn("11", message)
        self.assertIn("could not be deleted", message)
