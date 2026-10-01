# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.queue_job.job import Job


@tagged("post_install", "-at_install")
class TestApiRunnerCounters(TransactionCase):
    """The API runner counters must follow the stored job state.

    ``queue_job_cron_jobrunner`` ``_process()`` catches every exception raised
    by the job, stores it as failed (or pending, for a retry) and returns
    normally, so counting only the exceptions that escape ``_process()``
    reported business failures as successful runs.
    """

    def setUp(self):
        super().setUp()
        self.env["queue.job"].search([("state", "=", "pending")]).write({"state": "cancelled"})
        QueueJob = type(self.env["queue.job"])
        process = QueueJob._process

        def _process_no_commit(record, commit=False):
            return process(record, commit=False)

        patcher = patch.object(QueueJob, "_process", _process_no_commit)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _store_job(self, **kwargs):
        job = Job(self.env["queue.job"]._test_job, kwargs=kwargs)
        job.store()
        return job.db_record()

    def _assert_counters(self, result, **expected):
        self.assertEqual({key: result.get(key) for key in expected}, expected)

    def _run(self):
        return self.env["queue.job"]._api_job_runner(batch_size=10, max_seconds=30)

    def test_successful_job(self):
        record = self._store_job()
        result = self._run()
        self.assertEqual(record.state, "done")
        self._assert_counters(result, processed=1, done=1, failed=0, postponed=0)

    def test_business_failure(self):
        record = self._store_job(failure_rate=1)
        result = self._run()
        self.assertEqual(record.state, "failed")
        self._assert_counters(result, processed=1, done=0, failed=1, postponed=0)

    def test_retryable_failure(self):
        record = self._store_job(failure_rate=1, failure_retry_seconds=60)
        result = self._run()
        self.assertEqual(record.state, "pending")
        self._assert_counters(result, processed=1, done=0, failed=0, postponed=1)

    def test_mixed_batch(self):
        records = (
            self._store_job()
            | self._store_job(failure_rate=1)
            | self._store_job(failure_rate=1, failure_retry_seconds=60)
            | self._store_job()
        )
        result = self._run()
        self.assertEqual(records.mapped("state"), ["done", "failed", "pending", "done"])
        self._assert_counters(result, processed=4, done=2, failed=1, postponed=1)
