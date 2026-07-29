# © 2026 Deltatech
# See README.rst file on addons root folder for license details
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCronTriggerDebounce(TransactionCase):
    """_cron_trigger must create one trigger per real need, not one per call."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cron = cls.env["ir.cron"].create(
            {
                "name": "Test Queue Runner",
                "model_id": cls.env.ref("queue_job.model_queue_job").id,
                "state": "code",
                "code": "True",
                "queue_job_runner": True,
            }
        )

    def cron_triggers(self):
        return self.env["ir.cron.trigger"].search([("cron_id", "=", self.cron.id)])

    def test_repeated_calls_are_debounced(self):
        res_first = self.env["queue.job"]._cron_trigger()
        self.assertEqual(res_first, "triggered")
        self.assertEqual(len(self.cron_triggers()), 1)

        # the pending trigger covers the second request
        res_second = self.env["queue.job"]._cron_trigger()
        self.assertEqual(len(self.cron_triggers()), 1)
        self.assertIn(res_second, ("exists", "triggered"))  # other runner crons may still trigger

    def test_eta_list_creates_single_covering_trigger(self):
        now = fields.Datetime.now()
        etas = [now + timedelta(minutes=10), now + timedelta(minutes=2), now + timedelta(minutes=30)]

        self.env["queue.job"]._cron_trigger(at=etas)

        triggers = self.cron_triggers()
        # the earliest ETA covers the later ones
        self.assertEqual(len(triggers), 1)
        self.assertAlmostEqual((triggers.call_at - (now + timedelta(minutes=2))).total_seconds(), 0, delta=60)

    def test_past_eta_is_clamped_to_now(self):
        now = fields.Datetime.now()

        self.env["queue.job"]._cron_trigger(at=[now - timedelta(hours=1)])

        triggers = self.cron_triggers()
        self.assertEqual(len(triggers), 1)
        self.assertGreaterEqual(triggers.call_at, now - timedelta(seconds=1))

    def test_far_trigger_does_not_cover_immediate_request(self):
        far = fields.Datetime.now() + timedelta(hours=2)
        self.env["queue.job"]._cron_trigger(at=far)
        self.assertEqual(len(self.cron_triggers()), 1)

        # an immediate request is NOT satisfied by a trigger two hours away
        self.env["queue.job"]._cron_trigger()
        self.assertEqual(len(self.cron_triggers()), 2)

    def test_single_datetime_argument(self):
        at = fields.Datetime.now() + timedelta(minutes=5)

        res = self.env["queue.job"]._cron_trigger(at=at)

        self.assertEqual(res, "triggered")
        triggers = self.cron_triggers()
        self.assertEqual(len(triggers), 1)
        self.assertAlmostEqual((triggers.call_at - at).total_seconds(), 0, delta=1)
