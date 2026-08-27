# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""A neutralized database -- every staging build restored on odoo.sh -- has all its
crons switched off by base/data/neutralize.sql, except base.autovacuum_job. Another
module's neutralize.sql cannot switch one back on either: neutralize_database()
iterates the installed modules in the arbitrary order Postgres returns them, so
base's blanket disable may run last. Hanging the cleanups off the autovacuum job is
therefore the only order-independent way a restored copy can tidy itself up.
"""

import base64
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAutovacuumCleanup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env["ir.config_parameter"].sudo()
        cls.partner = cls.env["res.partner"].create({"name": "Autovacuum Customer"})
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})

    def _old_pdf(self, name, days_ago=200):
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "sale.order",
                "res_id": self.order.id,
                "type": "binary",
                "datas": base64.b64encode(b"pdf"),
                "mimetype": "application/pdf",
            }
        )
        past = datetime.utcnow() - timedelta(days=days_ago)
        self.env.cr.execute("UPDATE ir_attachment SET create_date = %s WHERE id = %s", (past, att.id))
        self.env["ir.attachment"].invalidate_model(["create_date"])
        return att

    def test_disabled_by_default(self):
        """The switch is off unless someone sets it, so adding the hook changes
        nothing for an existing customer."""
        self.icp.search([("key", "=", "deltatech_actions.autovacuum_enabled")]).unlink()
        att = self._old_pdf("Oferta - S0001.pdf")
        self.assertIsNone(self.env["sale.order"]._gc_generated_pdfs())
        self.assertTrue(att.exists(), "autovacuum deleted an attachment while switched off")

    def test_enabled_deletes_and_reports_progress(self):
        self.icp.set_param("deltatech_actions.autovacuum_enabled", "True")
        self.icp.set_param("deltatech_actions.sale_pdf_dry_run", "False")
        self.icp.set_param("deltatech_actions.sale_pdf_limit", "2")
        self.icp.set_param("deltatech_actions.sale_pdf_max_date_days", "90")
        self.icp.set_param("deltatech_actions.sale_pdf_pattern", "")
        kept = self._old_pdf("Recent offer.pdf", days_ago=1)
        self._old_pdf("Oferta - S0002.pdf")
        self._old_pdf("Oferta - S0003.pdf")

        done, remaining = self.env["sale.order"]._gc_generated_pdfs()
        self.assertEqual(done, 2, "should delete exactly one batch")
        self.assertTrue(remaining, "hitting the limit must ask the autovacuum job to requeue")
        self.assertTrue(kept.exists(), "an attachment newer than the threshold must survive")

    def test_dry_run_never_asks_to_be_requeued(self):
        """A dry run selects the same rows on every call. If it reported work
        remaining, _run_vacuum_cleaner would spin on it until the cron ran out of
        time, starving every other vacuum method."""
        self.icp.set_param("deltatech_actions.autovacuum_enabled", "True")
        self.icp.set_param("deltatech_actions.sale_pdf_dry_run", "True")
        self.icp.set_param("deltatech_actions.sale_pdf_limit", "1")
        self.icp.set_param("deltatech_actions.sale_pdf_max_date_days", "90")
        att = self._old_pdf("Oferta - S0004.pdf")

        done, remaining = self.env["sale.order"]._gc_generated_pdfs()
        self.assertEqual(done, 1)
        self.assertFalse(remaining, "a dry run must never report work remaining")
        self.assertTrue(att.exists(), "a dry run must not delete")

    def test_reports_the_batch_on_the_cron(self):
        """_run_vacuum_cleaner reports progress as _commit_progress() with no
        arguments, so the cron's `done` counter stays at zero however much the
        vacuum methods deleted. ir.cron._process_job then treats a job as failed
        when it timed out CONSECUTIVE_TIMEOUT_FOR_FAILURE times *and* done is
        zero, and _update_failure_count deactivates a cron that failed 5 times
        over 7 days -- which would switch Odoo's own autovacuum off, taking
        _gc_file_store with it. Reporting the real count makes that impossible.
        """
        self.icp.set_param("deltatech_actions.autovacuum_enabled", "True")
        self.icp.set_param("deltatech_actions.sale_pdf_dry_run", "False")
        self.icp.set_param("deltatech_actions.sale_pdf_limit", "5")
        self.icp.set_param("deltatech_actions.sale_pdf_max_date_days", "90")
        self._old_pdf("Oferta - S0005.pdf")
        reported = []

        def spy(cron_self, processed=0, **kwargs):
            # Does not call through: the real _commit_progress() commits, which a
            # test cursor forbids.
            reported.append(processed)
            return float("inf")

        # ir_cron_progress_id in the context is how the hook knows it is inside a
        # cron run; without it there is nothing to report progress to.
        orders = self.env["sale.order"].with_context(ir_cron_progress_id=1, cron_id=1)
        with patch.object(type(self.env["ir.cron"]), "_commit_progress", spy):
            done, _remaining = orders._gc_generated_pdfs()

        self.assertEqual(done, 1)
        self.assertEqual(reported, [1], "the batch size must reach the cron's progress counter")

    def test_no_requeue_when_the_run_is_nearly_out_of_time(self):
        """Asking for a requeue with seconds left only gets the next batch killed
        partway, and pushes the job over its time limit."""
        self.icp.set_param("deltatech_actions.autovacuum_enabled", "True")
        self.icp.set_param("deltatech_actions.sale_pdf_dry_run", "False")
        self.icp.set_param("deltatech_actions.sale_pdf_limit", "1")
        self.icp.set_param("deltatech_actions.sale_pdf_max_date_days", "90")
        self._old_pdf("Oferta - S0006.pdf")
        self._old_pdf("Oferta - S0007.pdf")

        orders = self.env["sale.order"].with_context(ir_cron_progress_id=1, cron_id=1)
        with patch.object(type(self.env["ir.cron"]), "_commit_progress", lambda *a, **kw: 0.0):
            done, remaining = orders._gc_generated_pdfs()

        self.assertEqual(done, 1, "the batch still runs")
        self.assertFalse(remaining, "must not ask for another batch with no time left")

    def test_hooks_are_registered_as_autovacuum(self):
        """_run_vacuum_cleaner finds these only through the decorator."""
        from odoo.addons.base.models.ir_autovacuum import is_autovacuum

        for model in ("sale.order", "account.move", "stock.picking"):
            with self.subTest(model=model):
                func = type(self.env[model])._gc_generated_pdfs
                self.assertTrue(is_autovacuum(func), f"{model}._gc_generated_pdfs is not an autovacuum method")


@tagged("post_install", "-at_install")
class TestNullFileSize(TransactionCase):
    """ir_attachment.file_size is nullable, and the cleanups sum it to report how much
    they freed. A single NULL row used to raise TypeError -- and inside the autovacuum
    job that failure is invisible: _run_vacuum_cleaner logs the exception, rolls the
    transaction back and moves on, so a crashing cleanup is indistinguishable from one
    with nothing to delete. Found on a real staging database, where it silently stopped
    the sale order cleanup dead.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env["ir.config_parameter"].sudo()
        cls.partner = cls.env["res.partner"].create({"name": "Null Size Customer"})
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})

    def test_cleanup_survives_a_null_file_size(self):
        att = self.env["ir.attachment"].create(
            {
                "name": "Oferta - S9999.pdf",
                "res_model": "sale.order",
                "res_id": self.order.id,
                "type": "binary",
                "datas": base64.b64encode(b"pdf"),
                "mimetype": "application/pdf",
            }
        )
        past = datetime.utcnow() - timedelta(days=200)
        self.env.cr.execute(
            "UPDATE ir_attachment SET create_date = %s, file_size = NULL WHERE id = %s",
            (past, att.id),
        )
        self.env["ir.attachment"].invalidate_model(["create_date", "file_size"])

        self.icp.set_param("deltatech_actions.sale_pdf_dry_run", "False")
        self.icp.set_param("deltatech_actions.sale_pdf_limit", "10")
        self.icp.set_param("deltatech_actions.sale_pdf_max_date_days", "90")
        self.icp.set_param("deltatech_actions.sale_pdf_pattern", "")

        summary = self.env["sale.order"].cron_clean_generated_pdfs_from_settings()

        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["size"], 0, "a NULL size must count as zero, not blow up")
        self.assertFalse(att.exists())
