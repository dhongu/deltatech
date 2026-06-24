# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestQueueJobIdentityKeyDedup(TransactionCase):
    def _enqueue(self, identity_key=None):
        """Enqueue a real job (with a valid uuid and records) and return it."""
        return self.env["queue.job"].with_delay(identity_key=identity_key)._test_job()

    def test_failed_duplicate_cancelled_on_new_job(self):
        """A new job cancels older failed jobs sharing the same identity_key."""
        identity = "deltatech_qj_dedup_test"

        failed = self._enqueue(identity_key=identity)
        failed_record = failed.db_record()
        failed.set_failed(exc_info="boom")
        failed.store()
        failed_record.invalidate_recordset(["state"])
        self.assertEqual(failed_record.state, "failed")

        new_job = self._enqueue(identity_key=identity)
        new_record = new_job.db_record()

        failed_record.invalidate_recordset(["state"])
        self.assertEqual(failed_record.state, "cancelled")
        self.assertEqual(new_record.state, "pending")
        self.assertNotEqual(failed_record.id, new_record.id)

    def test_failed_without_identity_key_is_kept(self):
        """A new job without identity_key must not touch existing failed jobs."""
        failed = self._enqueue()
        failed_record = failed.db_record()
        failed.set_failed(exc_info="boom")
        failed.store()

        self._enqueue()

        failed_record.invalidate_recordset(["state"])
        self.assertEqual(failed_record.state, "failed")
