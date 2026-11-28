# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
import uuid as uuid_lib
from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged

from odoo.addons.queue_job.delay import DelayableGraph
from odoo.addons.queue_job.job import CANCELLED, WAIT_DEPENDENCIES, Job


@tagged("post_install", "-at_install")
class TestDateCancelled(TransactionCase):
    """Joburile anulate în lanț trebuie să poată fi curățate de autovacuum.

    Vechiul ``Job.cancel_dependent_jobs()`` scria doar starea, printr-un UPDATE
    brut, iar curățarea standard selectează după ``date_done``/``date_cancelled``:
    fără dată, joburile rămâneau în tabel pentru totdeauna (189.644 pe o instanță
    de producție). `queue_job` aliniat cu OCA 20.0 pune data singur; rândurile
    rămase fără dată le curăță ``_gc_dateless_terminal_jobs()``.
    """

    def _create_job(self, state="cancelled", graph_uuid=None, channel="root"):
        return self.env["queue.job"].create(
            {
                "uuid": str(uuid_lib.uuid4()),
                "name": "Test Job",
                "model_name": "queue.job",
                "method_name": "search",
                "state": state,
                "graph_uuid": graph_uuid,
                "channel": channel,
            }
        )

    def _clear_dates(self, jobs):
        """Reproduce ce lăsa în urmă UPDATE-ul brut al vechiului cancel_dependent_jobs."""
        self.env.cr.execute(
            "UPDATE queue_job SET date_cancelled = NULL, date_done = NULL WHERE id IN %s",
            (tuple(jobs.ids),),
        )
        jobs.invalidate_recordset(["date_cancelled", "date_done"])

    def test_chain_cancel_stamps_date_cancelled(self):
        """Anularea în lanț lasă o dată de anulare pe dependenți.

        O face acum `queue_job` (OCA 20.0); testul rămâne ca joburile anulate în
        lanț să nu se mai adune în tabel dacă `queue_job` ar regresa.
        """
        job_root = Job(self.env["queue.job"].search)
        job_child = Job(self.env["queue.job"].search)
        job_child.add_depends({job_root})
        DelayableGraph._ensure_same_graph_uuid([job_root, job_child])
        job_root.store()
        job_child.store()
        record_child = job_child.db_record()
        self.assertEqual(record_child.state, WAIT_DEPENDENCIES)

        job_root.db_record().button_cancelled()

        self.assertEqual(record_child.state, CANCELLED)
        self.assertTrue(record_child.date_cancelled, "Anularea în lanț trebuie să lase o dată de anulare.")

    def test_gc_removes_dateless_terminal_jobs(self):
        """Joburile terminale rămase fără dată sunt curățate."""
        channel = self.env["queue.job.channel"].search([("complete_name", "=", "root")], limit=1)
        old = self._create_job(channel="root")
        self._clear_dates(old)
        self.env.cr.execute(
            "UPDATE queue_job SET date_created = %s WHERE id = %s",
            (datetime.now() - timedelta(days=int(channel.removal_interval) + 1), old.id),
        )
        old_id = old.id

        self.env["queue.job"]._gc_dateless_terminal_jobs()

        self.assertFalse(self.env["queue.job"].browse(old_id).exists())

    def test_gc_keeps_recent_dateless_jobs(self):
        """Un job terminal recent fără dată rămâne — poate fi încă util."""
        recent = self._create_job(channel="root")
        self._clear_dates(recent)
        recent_id = recent.id

        self.env["queue.job"]._gc_dateless_terminal_jobs()

        self.assertTrue(self.env["queue.job"].browse(recent_id).exists())
