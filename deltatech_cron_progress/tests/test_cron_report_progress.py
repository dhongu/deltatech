# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCronReportProgress(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cron = cls.env["ir.cron"].create(
            {
                "name": "Test cron progress",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "state": "code",
                "code": "pass",
                "interval_number": 1,
                "interval_type": "days",
                "active": True,
            }
        )

    def _triggers(self, cron):
        return self.env["ir.cron.trigger"].search([("cron_id", "=", cron.id)])

    # --- cron run (scheduler or "Run manually"): cron_id + ir_cron_progress_id -------------------
    # _commit_progress commits, so these run on a separate test cursor, like the Odoo tests

    def _report_in_cron(self, done, remaining, deactivate=False):
        """Call the helper in the context of a cron run; return (result, progress values)."""
        with self.enter_registry_test_mode(), self.registry.cursor() as cr:
            cron = self.cron.with_env(self.cron.env(cr=cr, context={"cron_id": self.cron.id}))
            cron, progress = cron._add_progress()
            result = cron.env["ir.cron"]._cron_report_progress(done, remaining, deactivate=deactivate)
            values = (progress.done, progress.remaining, progress.deactivate)
        return result, values

    def test_cron_run_reports_progress_without_trigger(self):
        result, values = self._report_in_cron(5, 3)
        self.assertEqual(result, 3)
        self.assertEqual(values, (5, 3, False))
        # the scheduler loop takes care of the rest
        self.assertFalse(self._triggers(self.cron))

    def test_cron_run_no_progress_stops_loop(self):
        result, values = self._report_in_cron(0, 7)
        self.assertEqual(result, 0)
        self.assertEqual(values, (0, 0, False))
        self.assertFalse(self._triggers(self.cron))

    def test_cron_run_deactivate(self):
        _result, values = self._report_in_cron(4, 0, deactivate=True)
        self.assertEqual(values, (4, 0, True))

    def test_cron_run_loops_until_done(self):
        """The scheduler runs the job again while the helper reports remaining records."""
        batches = iter([(2, 3), (2, 1), (1, 0)])
        calls = self._process_job_reporting(lambda env: env["ir.cron"]._cron_report_progress(*next(batches)))
        self.assertEqual(len(calls), 3)
        self.assertFalse(self._triggers(self.cron))

    def _process_job_reporting(self, report):
        """Run the cron job once through the scheduler; ``report(env)`` reports the batch."""
        calls = []

        def mocked_run(action):
            calls.append(1)
            report(action.env)

        job_values = {"done": 0, "remaining": 0, "timed_out_counter": 0}
        self.env.flush_all()
        with (
            self.enter_registry_test_mode(),
            patch.object(self.registry["ir.actions.server"], "run", mocked_run),
            self.registry.cursor() as cr,
        ):
            self.registry["ir.cron"]._process_job(cr, {**self.cron.read(load=None)[0], **job_values})
        return calls

    def test_cron_run_no_progress_is_not_rescheduled(self):
        """A batch that processes nothing ends the run, without an ASAP reschedule."""
        calls = self._process_job_reporting(lambda env: env["ir.cron"]._cron_report_progress(0, 5))
        self.assertEqual(len(calls), 1)
        self.assertFalse(self._triggers(self.cron))

    def test_native_no_progress_is_rescheduled(self):
        """Control: reporting remaining records without progress natively reschedules ASAP."""
        calls = self._process_job_reporting(lambda env: env["ir.cron"]._commit_progress(0, remaining=5))
        self.assertEqual(len(calls), 1)
        self.assertTrue(self._triggers(self.cron))

    # --- direct call from code: no progress in context, nothing is committed --------------------

    def test_direct_call_triggers_given_cron(self):
        result = self.cron._cron_report_progress(5, 3)
        self.assertEqual(result, 3)
        self.assertEqual(len(self._triggers(self.cron)), 1)

    def test_direct_call_without_cron(self):
        # nothing to report and nothing to trigger, but no error either
        result = self.env["ir.cron"]._cron_report_progress(5, 3)
        self.assertEqual(result, 3)
        self.assertFalse(self.env["ir.cron.progress"].search([("cron_id", "=", self.cron.id)]))

    def test_direct_call_no_progress(self):
        self.assertEqual(self.cron._cron_report_progress(0, 3), 0)
        self.assertFalse(self._triggers(self.cron))

    def test_direct_call_inactive_cron(self):
        # Odoo skips immediate triggers on inactive crons
        self.cron.active = False
        self.cron._cron_report_progress(5, 3)
        self.assertFalse(self._triggers(self.cron))

    def test_direct_call_non_admin_user(self):
        user = self.env["res.users"].create({"name": "Cron progress user", "login": "cron_progress_user"})
        self.cron.with_user(user)._cron_report_progress(2, 1)
        self.assertEqual(len(self._triggers(self.cron)), 1)
