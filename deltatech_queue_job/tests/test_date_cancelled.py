# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
import uuid as uuid_lib
from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged

from odoo.addons.queue_job.job import Job


@tagged("post_install", "-at_install")
class TestDateCancelled(TransactionCase):
    """Joburile anulate în lanț trebuie să poată fi curățate de autovacuum.

    ``Job.cancel_dependent_jobs()`` scrie doar starea, printr-un UPDATE brut, iar
    cronul de autovacuum selectează după ``date_done``/``date_cancelled``: fără
    dată, joburile rămâneau în tabel pentru totdeauna (189.644 pe o instanță de
    producție).
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
        """Reproduce ce lăsa în urmă UPDATE-ul brut din cancel_dependent_jobs."""
        self.env.cr.execute(
            "UPDATE queue_job SET date_cancelled = NULL, date_done = NULL WHERE id IN %s",
            (tuple(jobs.ids),),
        )
        jobs.invalidate_recordset(["date_cancelled", "date_done"])

    def test_patch_stamps_date_cancelled(self):
        """După anularea dependenților, joburile anulate din graf au dată."""
        graph = str(uuid_lib.uuid4())
        parent = self._create_job(graph_uuid=graph)
        child = self._create_job(graph_uuid=graph)
        self._clear_dates(parent | child)
        self.assertFalse(child.date_cancelled)

        Job.load(self.env, parent.uuid).cancel_dependent_jobs()

        child.invalidate_recordset(["date_cancelled"])
        self.assertTrue(child.date_cancelled, "Anularea în lanț trebuie să lase o dată de anulare.")

    def test_patch_ignores_jobs_outside_the_graph(self):
        """Joburile din alt graf nu sunt atinse."""
        graph = str(uuid_lib.uuid4())
        parent = self._create_job(graph_uuid=graph)
        strain = self._create_job(graph_uuid=str(uuid_lib.uuid4()))
        self._clear_dates(parent | strain)

        Job.load(self.env, parent.uuid).cancel_dependent_jobs()

        strain.invalidate_recordset(["date_cancelled"])
        self.assertFalse(strain.date_cancelled)

    def test_autovacuum_removes_dateless_terminal_jobs(self):
        """Joburile terminale fără dată, dinainte de patch, sunt curățate."""
        channel = self.env["queue.job.channel"].search([("complete_name", "=", "root")], limit=1)
        old = self._create_job(channel="root")
        self._clear_dates(old)
        self.env.cr.execute(
            "UPDATE queue_job SET date_created = %s WHERE id = %s",
            (datetime.now() - timedelta(days=int(channel.removal_interval) + 1), old.id),
        )
        old_id = old.id

        self.env["queue.job"].autovacuum()

        self.assertFalse(self.env["queue.job"].browse(old_id).exists())

    def test_autovacuum_keeps_recent_dateless_jobs(self):
        """Un job terminal recent fără dată rămâne — poate fi încă util."""
        recent = self._create_job(channel="root")
        self._clear_dates(recent)
        recent_id = recent.id

        self.env["queue.job"].autovacuum()

        self.assertTrue(self.env["queue.job"].browse(recent_id).exists())
