# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCronCleanOldMessages(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create three messages with different models/subjects
        cls.msg1 = cls.env["mail.message"].create(
            {
                "subject": "LOG_001",
                "body": "Test body",
                "model": "stock.picking",
                "res_id": 0,
            }
        )
        cls.msg2 = cls.env["mail.message"].create(
            {
                "subject": "OTHER_001",
                "body": "Test body",
                "model": "stock.picking",
                "res_id": 0,
            }
        )
        cls.msg3 = cls.env["mail.message"].create(
            {
                "subject": "LOG_002",
                "body": "Test body",
                "model": "sale.order",
                "res_id": 0,
            }
        )

        # Attachments for msg1: one PDF (should be deleted), one XML (should be kept)
        cls.att_pdf = cls.env["ir.attachment"].create(
            {
                "name": "LOG_001.pdf",
                "res_model": "mail.message",
                "res_id": cls.msg1.id,
                "type": "binary",
                "datas": __import__("base64").b64encode(b"pdf"),
                "mimetype": "application/pdf",
            }
        )
        cls.att_xml = cls.env["ir.attachment"].create(
            {
                "name": "LOG_001.xml",
                "res_model": "mail.message",
                "res_id": cls.msg1.id,
                "type": "binary",
                "datas": __import__("base64").b64encode(b"<xml/>"),
                "mimetype": "application/xml",
            }
        )

        # Make messages old enough to be selected by the cron (older than 1 day)
        past_dt = datetime.utcnow() - timedelta(days=30)
        for mid in (cls.msg1.id, cls.msg2.id, cls.msg3.id):
            cls.env.cr.execute("UPDATE mail_message SET create_date = %s WHERE id = %s", (past_dt, mid))

    def test_cron_clean_old_messages_dry_run(self):
        # Dry run: nothing should be deleted
        self.env["mail.message"].cron_clean_old_messages(
            limit=100,
            pattern="LOG_%",
            max_date_days=1,
            dry_run=True,
            exclude_models=["business.%"],
        )
        self.assertTrue(self.msg1.exists())
        self.assertTrue(self.msg2.exists())
        self.assertTrue(self.msg3.exists())
        self.assertTrue(self.att_pdf.exists())
        self.assertTrue(self.att_xml.exists())

    def test_cron_clean_old_messages_real_run(self):
        # Real run: should delete msg1 (matches pattern, not excluded),
        # keep msg2 (pattern doesn't match), keep msg3 (excluded model)
        self.env["mail.message"].cron_clean_old_messages(
            limit=100,
            pattern="LOG_%",
            max_date_days=1,
            dry_run=False,
            exclude_models=["business.%"],
        )

        # msg1 deleted, msg2 and msg3 remain
        self.assertFalse(self.msg1.exists())
        self.assertTrue(self.msg2.exists())

        # Attachments: PDF should be deleted, XML should be preserved
        self.assertFalse(self.att_pdf.exists())

    def test_cron_clean_old_messages_exclude_models(self):
        # every excluded pattern is honoured (NOT LIKE ANY kept only the messages matching all patterns)
        self.env["mail.message"].cron_clean_old_messages(
            limit=100,
            pattern="LOG_%",
            max_date_days=1,
            dry_run=False,
            exclude_models=["business.%", "sale.%"],
        )
        self.assertFalse(self.msg1.exists())
        self.assertTrue(self.msg3.exists())

    def test_cron_clean_old_messages_no_exclude_models(self):
        # exclude_models=False must not raise an SQL error
        self.env["mail.message"].cron_clean_old_messages(
            limit=100, pattern="LOG_%", max_date_days=1, dry_run=False, exclude_models=False
        )
        self.assertFalse(self.msg1.exists())
        self.assertFalse(self.msg3.exists())
        self.assertTrue(self.msg2.exists())

    def test_cron_clean_old_messages_fix_xml_mimetype(self):
        att = self.env["ir.attachment"].create({"name": "factura.xml", "raw": b"<xml/>", "mimetype": "text/plain"})
        self.env.cr.execute("UPDATE ir_attachment SET mimetype = 'text/plain' WHERE id = %s", (att.id,))
        self.env["mail.message"].cron_clean_old_messages(limit=1, pattern="NONE_%", max_date_days=1, dry_run=True)
        att.invalidate_recordset(["mimetype"])
        self.assertEqual(att.mimetype, "application/xml")

    def _progress(self):
        cron = self.env.ref("deltatech_actions.ir_cron_delete_mail_messages")
        cron.active = True
        return cron._add_progress()

    def test_cron_clean_old_messages_progress(self):
        cron, progress = self._progress()
        Message = self.env["mail.message"].with_context(ir_cron_progress_id=progress.id)
        Message.cron_clean_old_messages(limit=1, pattern="LOG_%", max_date_days=1, dry_run=False)
        self.assertEqual((progress.done, progress.remaining), (1, 1))
        # manual run: the rest is processed in the background
        self.assertTrue(self.env["ir.cron.trigger"].search([("cron_id", "=", cron.id)]))

    def test_cron_clean_old_messages_dry_run_progress(self):
        cron, progress = self._progress()
        Message = self.env["mail.message"].with_context(ir_cron_progress_id=progress.id)
        Message.cron_clean_old_messages(limit=1, pattern="LOG_%", max_date_days=1, dry_run=True)
        # dry run never advances: no loop
        self.assertEqual((progress.done, progress.remaining), (0, 0))
        self.assertFalse(self.env["ir.cron.trigger"].search([("cron_id", "=", cron.id)]))
