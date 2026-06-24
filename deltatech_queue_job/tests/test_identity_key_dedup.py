# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo.tests import TransactionCase, tagged

from odoo.addons.queue_job.job import Job


@tagged("post_install", "-at_install")
class TestQueueJobIdentityKeyDedup(TransactionCase):
    def _store_job(self, identity_key=None, state=None):
        """Persist a real queue.job record (with a valid uuid) and return it.

        Built directly through ``Job`` so it is stored regardless of the
        ``QUEUE_JOB__NO_DELAY`` test mode (where ``with_delay`` would run
        inline and never create a record).
        """
        job = Job(self.env["queue.job"]._test_job, identity_key=identity_key)
        if state == "failed":
            job.set_failed(exc_info="boom")
        job.store()
        return job

    def test_failed_duplicate_cancelled_on_new_job(self):
        """A new job cancels older failed jobs sharing the same identity_key."""
        identity = "deltatech_qj_dedup_test"

        failed = self._store_job(identity_key=identity, state="failed")
        failed_record = failed.db_record()
        self.assertEqual(failed_record.state, "failed")

        new_job = self._store_job(identity_key=identity)
        new_record = new_job.db_record()

        failed_record.invalidate_recordset(["state"])
        self.assertEqual(failed_record.state, "cancelled")
        self.assertEqual(new_record.state, "pending")
        self.assertNotEqual(failed_record.id, new_record.id)

    def test_failed_without_identity_key_is_kept(self):
        """A new job without identity_key must not touch existing failed jobs."""
        failed = self._store_job(state="failed")
        failed_record = failed.db_record()

        self._store_job()

        failed_record.invalidate_recordset(["state"])
        self.assertEqual(failed_record.state, "failed")
