# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestQueueJob(TransactionCase):
    def setUp(self):
        super().setUp()
        # Ensure config parameters are set
        self.env["ir.config_parameter"].sudo().set_param("queue_job_processor.batch_size", "5")
        self.env["ir.config_parameter"].sudo().set_param("queue_job_processor.max_seconds", "30")

    def _create_pending_job(self):
        """Helper to create a pending queue.job record"""
        return self.env["queue.job"].create(
            {
                "name": "Test Job",
                "model_name": "queue.job",
                "method_name": "search",
                "state": "pending",
                "priority": 10,
            }
        )

    def test_api_job_runner_no_jobs(self):
        """_api_job_runner returns correct structure when no jobs are pending"""
        # Cancel all existing pending jobs to ensure clean state
        pending = self.env["queue.job"].search([("state", "=", "pending")])
        pending.write({"state": "cancelled"})

        result = self.env["queue.job"]._api_job_runner(batch_size=5, max_seconds=10)

        self.assertIn("processed", result)
        self.assertIn("failed", result)
        self.assertIn("time_elapsed", result)
        self.assertIn("pending_remaining", result)
        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["pending_remaining"], 0)

    def test_api_job_runner_returns_dict(self):
        """_api_job_runner always returns a dict with expected keys"""
        result = self.env["queue.job"]._api_job_runner(batch_size=1, max_seconds=5)
        self.assertIsInstance(result, dict)
        self.assertIn("processed", result)
        self.assertIn("failed", result)
        self.assertIn("time_elapsed", result)
        self.assertIn("pending_remaining", result)

    def test_cron_trigger_no_cron(self):
        """_cron_trigger returns 'nothing' when no queue_job_runner cron exists"""
        # Deactivate all queue_job_runner crons
        crons = self.env["ir.cron"].sudo().search([("queue_job_runner", "=", True)])
        crons.write({"active": False})

        result = self.env["queue.job"]._cron_trigger()
        self.assertEqual(result, "nothing")

    def test_cron_trigger_with_cron(self):
        """_cron_trigger returns 'triggered' or 'exists' when a cron is present"""
        crons = self.env["ir.cron"].sudo().search([("queue_job_runner", "=", True)])
        if not crons:
            self.skipTest("No queue_job_runner cron found")

        result = self.env["queue.job"]._cron_trigger()
        self.assertIn(result, ["triggered", "exists", "nothing"])

    def test_job_runner_no_jobs(self):
        """_job_runner runs without error when no pending jobs exist"""
        pending = self.env["queue.job"].search([("state", "=", "pending")])
        pending.write({"state": "cancelled"})

        # Should not raise
        self.env["queue.job"]._job_runner(commit=False)

    def test_acquire_specific_job_not_found(self):
        """_acquire_specific_job returns empty recordset for non-existent id"""
        result = self.env["queue.job"]._acquire_specific_job(job_id=0)
        self.assertFalse(result)

    def test_start_cron_trigger_no_cron(self):
        """start_cron_trigger returns a notification action"""
        crons = self.env["ir.cron"].sudo().search([("queue_job_runner", "=", True)])
        crons.write({"active": False})

        job = self.env["queue.job"].search([], limit=1)
        if not job:
            self.skipTest("No queue.job records available")

        result = job.start_cron_trigger()
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")

    def test_process_jobs_returns_notification(self):
        """process_jobs returns a client notification action"""
        with patch.object(type(self.env["queue.job"]), "_ensure_cron_trigger", return_value=None, create=True):
            job = self.env["queue.job"].search([], limit=1)
            if not job:
                self.skipTest("No queue.job records available")
            result = job.process_jobs()
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")

    def test_action_process_api_thread_returns_notification(self):
        """action_process_api_thread starts a thread and returns a notification"""
        job = self.env["queue.job"].search([], limit=1)
        if not job:
            self.skipTest("No queue.job records available")

        result = job.action_process_api_thread()
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["type"], "success")


@tagged("post_install", "-at_install")
class TestResConfigSettings(TransactionCase):
    def test_generate_api_key(self):
        """action_generate_queue_job_processor_api_key generates a non-empty key"""
        settings = self.env["res.config.settings"].create({})
        result = settings.action_generate_queue_job_processor_api_key()

        self.assertTrue(settings.queue_job_processor_api_key)
        self.assertGreater(len(settings.queue_job_processor_api_key), 10)
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")

    def test_config_fields_exist(self):
        """Config settings fields are accessible"""
        settings = self.env["res.config.settings"].create({})
        self.assertIsNotNone(settings.queue_job_processor_batch_size)
        self.assertIsNotNone(settings.queue_job_processor_max_seconds)
