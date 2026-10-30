# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

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
        cls.other_cron = cls.cron.copy({"name": "Test cron progress (copy)"})

    def _triggers(self, cron):
        return self.env["ir.cron.trigger"].search([("cron_id", "=", cron.id)])

    def _progress_env(self, scheduler):
        """Return (ir.cron model, progress) with the context of a scheduler or manual run."""
        cron, progress = self.cron._add_progress()
        context = {"ir_cron_progress_id": progress.id}
        if scheduler:
            context["cron_id"] = self.cron.id
        return self.env["ir.cron"].with_context(**context), progress

    # --- scheduler run: cron_id + ir_cron_progress_id -------------------------------------------

    def test_scheduler_reports_progress_without_trigger(self):
        IrCron, progress = self._progress_env(scheduler=True)
        result = IrCron._cron_report_progress(5, 3)
        self.assertEqual(result, 3)
        self.assertEqual((progress.done, progress.remaining), (5, 3))
        # the scheduler loop takes care of the rest
        self.assertFalse(self._triggers(self.cron))

    def test_scheduler_no_progress_stops_loop(self):
        IrCron, progress = self._progress_env(scheduler=True)
        result = IrCron._cron_report_progress(0, 7)
        self.assertEqual(result, 0)
        self.assertEqual((progress.done, progress.remaining), (0, 0))
        self.assertFalse(self._triggers(self.cron))

    def test_scheduler_deactivate(self):
        IrCron, progress = self._progress_env(scheduler=True)
        IrCron._cron_report_progress(4, 0, deactivate=True)
        self.assertEqual((progress.done, progress.remaining), (4, 0))
        self.assertTrue(progress.deactivate)

    # --- manual run ("Run manually", webhook): only ir_cron_progress_id -------------------------

    def test_manual_run_triggers_progress_cron(self):
        IrCron, progress = self._progress_env(scheduler=False)
        # the cron is taken from the progress, not from the recordset the helper is called on
        IrCron.browse(self.other_cron.id)._cron_report_progress(5, 3)
        self.assertEqual((progress.done, progress.remaining), (5, 3))
        self.assertEqual(len(self._triggers(self.cron)), 1)
        self.assertFalse(self._triggers(self.other_cron))

    def test_manual_run_done(self):
        IrCron, progress = self._progress_env(scheduler=False)
        IrCron._cron_report_progress(5, 0)
        self.assertEqual((progress.done, progress.remaining), (5, 0))
        self.assertFalse(self._triggers(self.cron))

    def test_manual_run_no_progress(self):
        IrCron, progress = self._progress_env(scheduler=False)
        IrCron._cron_report_progress(0, 3)
        self.assertEqual(progress.remaining, 0)
        self.assertFalse(self._triggers(self.cron))

    # --- direct call from code: no progress in context -------------------------------------------

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
