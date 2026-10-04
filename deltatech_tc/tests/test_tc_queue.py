import json
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestTcQueue(TransactionCase):
    """Claim, lost-result recovery, manual retry and cleanup of the job queue."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.station = cls.env["deltatech.tc.station"].create({"name": "Queue Station"})
        cls.other = cls.env["deltatech.tc.station"].create({"name": "Other Station"})
        cls.Job = cls.env["deltatech.tc.job"]

    def _job(self, job_type="ping", station=None, **vals):
        return self.Job.create({"station_id": (station or self.station).id, "job_type": job_type, **vals})

    def _http(self, method):
        return self._job("http_request", payload=json.dumps({"url": "http://192.168.1.50/x", "method": method}))

    def _age_claim(self, job, minutes):
        job.write({"claimed_at": fields.Datetime.now() - timedelta(minutes=minutes)})

    def _set_param(self, key, value):
        self.env["ir.config_parameter"].sudo().set_str(f"deltatech_tc.{key}", value)

    # ------------------------------------------------------------------
    # claim
    # ------------------------------------------------------------------
    def test_claim_marks_claimed_counts_attempt_and_respects_limit(self):
        jobs = self._job() | self._job() | self._job()
        foreign = self._job(station=self.other)
        claimed = self.Job._claim_for_station(self.station, limit=2)
        self.assertEqual(claimed, jobs[:2], "Oldest first, only this station's, at most `limit`.")
        self.assertEqual(set(claimed.mapped("state")), {"claimed"})
        self.assertEqual(claimed.mapped("attempt_count"), [1, 1])
        self.assertTrue(all(claimed.mapped("claimed_at")))
        self.assertEqual(jobs[2].state, "pending")
        self.assertEqual(foreign.state, "pending")

    def test_claim_does_not_hand_out_claimed_jobs_again(self):
        job = self._job()
        self.Job._claim_for_station(self.station)
        self.assertFalse(self.Job._claim_for_station(self.station), "A fresh claim must not be re-offered.")
        self.assertEqual(job.attempt_count, 1)

    # ------------------------------------------------------------------
    # lost results
    # ------------------------------------------------------------------
    def test_retry_safe_job_is_offered_again_after_timeout(self):
        job = self._job("ping")
        self.Job._claim_for_station(self.station)
        self._age_claim(job, 16)
        again = self.Job._claim_for_station(self.station)
        self.assertEqual(again, job)
        self.assertEqual(job.state, "claimed")
        self.assertEqual(job.attempt_count, 2)

    def test_retry_safe_job_fails_after_max_attempts(self):
        self._set_param("max_attempts", "2")
        job = self._job("ping")
        for _i in range(2):
            self.Job._claim_for_station(self.station)
            self._age_claim(job, 16)
        self.assertFalse(self.Job._claim_for_station(self.station))
        self.assertEqual(job.state, "error")
        self.assertIn("2 attempts", job.error)
        self.assertTrue(job.done_at)

    def test_unsafe_job_stays_claimed_so_a_late_result_is_accepted(self):
        post = self._http("POST")
        self.Job._claim_for_station(self.station)
        self._age_claim(post, 60)
        self.assertFalse(self.Job._claim_for_station(self.station), "A POST must never run twice on its own.")
        self.assertEqual(post.state, "claimed")
        self.assertEqual(post.attempt_count, 1)
        post._store_result("done", result=json.dumps({"status": 200}))
        self.assertEqual(post.state, "done")

    def test_retry_safety_by_type_and_method(self):
        self.assertTrue(self._job("ping")._tc_is_retry_safe())
        self.assertTrue(self._http("GET")._tc_is_retry_safe())
        self.assertTrue(self._http("head")._tc_is_retry_safe())
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            self.assertFalse(self._http(method)._tc_is_retry_safe(), method)

    def test_timeout_zero_disables_recovery(self):
        self._set_param("claim_timeout_minutes", "0")
        job = self._job("ping")
        self.Job._claim_for_station(self.station)
        self._age_claim(job, 600)
        self.assertFalse(self.Job._claim_for_station(self.station))
        self.assertEqual(job.state, "claimed")

    def test_other_station_lost_jobs_are_not_touched(self):
        job = self._job("ping", station=self.other)
        self.Job._claim_for_station(self.other)
        self._age_claim(job, 60)
        self.Job._claim_for_station(self.station)
        self.assertEqual(job.state, "claimed")

    def test_bad_param_falls_back_to_default(self):
        self._set_param("claim_timeout_minutes", "abc")
        # get_int() logs the invalid value before falling back
        with self.assertLogs("odoo.addons.base.models.ir_config_parameter", "WARNING"):
            self.assertEqual(self.Job._tc_param("claim_timeout_minutes", 15), 15)
        self._set_param("claim_timeout_minutes", "-5")
        self.assertEqual(self.Job._tc_param("claim_timeout_minutes", 15), 0)

    # ------------------------------------------------------------------
    # manual retry
    # ------------------------------------------------------------------
    def test_retry_resets_error_and_stuck_jobs(self):
        failed = self._job()
        stuck = self._http("POST")
        self.Job._claim_for_station(self.station)
        failed._store_result("error", error="boom")
        (failed | stuck).action_retry()
        for job in failed | stuck:
            self.assertEqual(job.state, "pending")
            self.assertEqual(job.attempt_count, 0)
            self.assertFalse(job.error or job.claimed_at or job.done_at)

    def test_retry_leaves_done_jobs_alone(self):
        job = self._job()
        self.Job._claim_for_station(self.station)
        job._store_result("done", result="pong")
        job.action_retry()
        self.assertEqual(job.state, "done")
        self.assertEqual(job.result, "pong")

    def test_retry_requires_write_access(self):
        user = new_test_user(self.env, login="tc_reader", groups="deltatech_tc.group_deltatech_tc_user")
        job = self._http("POST")
        job._store_result("error", error="boom")
        with self.assertRaises(AccessError):
            job.with_user(user).action_retry()
        self.assertEqual(job.state, "error")

    # ------------------------------------------------------------------
    # cleanup
    # ------------------------------------------------------------------
    def test_gc_deletes_old_finished_jobs_only(self):
        now = fields.Datetime.now()
        old_done = self._job(state="done", done_at=now - timedelta(days=31))
        new_done = self._job(state="done", done_at=now - timedelta(days=5))
        old_error = self._job(state="error", done_at=now - timedelta(days=91))
        new_error = self._job(state="error", done_at=now - timedelta(days=31))
        pending = self._job()
        claimed = self._job(state="claimed", claimed_at=now - timedelta(days=200))
        self.Job._gc_jobs()
        self.assertFalse(old_done.exists())
        self.assertFalse(old_error.exists())
        self.assertEqual((new_done | new_error | pending | claimed).exists(), new_done | new_error | pending | claimed)

    def test_gc_counts_jobs_without_done_at_from_creation(self):
        job = self._job(state="error")
        self.env.cr.execute(
            "UPDATE deltatech_tc_job SET create_date = %s WHERE id = %s",
            (fields.Datetime.now() - timedelta(days=100), job.id),
        )
        job.invalidate_recordset()
        self.Job._gc_jobs()
        self.assertFalse(job.exists())

    def test_gc_expires_pending_only_when_enabled(self):
        job = self._job()
        self.env.cr.execute(
            "UPDATE deltatech_tc_job SET create_date = %s WHERE id = %s",
            (fields.Datetime.now() - timedelta(hours=48), job.id),
        )
        job.invalidate_recordset()
        self.Job._gc_jobs()
        self.assertEqual(job.state, "pending", "Pending jobs do not expire by default.")
        self._set_param("pending_ttl_hours", "24")
        self.Job._gc_jobs()
        self.assertEqual(job.state, "error")
        self.assertIn("24 hours", job.error)

    def test_cron_is_installed(self):
        cron = self.env.ref("deltatech_tc.ir_cron_deltatech_tc_gc_jobs")
        self.assertEqual(cron.code, "model._gc_jobs()")
