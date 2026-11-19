import json
from unittest.mock import patch

from odoo.tests import HttpCase, tagged


def _tc_store_default_env(self, job):
    """Stand-in callback: records the transaction's default env.

    Flushes (savepoint exit, the request's commit) recompute fields in that env, so
    it must have a user and a company; ``env.company`` raises ``IndexError`` otherwise.
    """
    default_env = self.env.cr.transaction.default_env
    self.ref = f"{default_env.uid}:{default_env.company.id}"


@tagged("post_install", "-at_install")
class TestDeltatechTc(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.station = cls.env["deltatech.tc.station"].create({"name": "Test Station"})

    def _post(self, path, body, key=None):
        headers = {"Content-Type": "application/json"}
        if key is not None:
            headers["X-Station-Key"] = key
        return self.url_open(path, data=json.dumps(body).encode(), headers=headers)

    def test_api_key_generated(self):
        self.assertTrue(self.station.api_key, "An API key must be generated on create")

    def test_authenticate(self):
        Station = self.env["deltatech.tc.station"]
        self.assertEqual(Station._authenticate(self.station.api_key), self.station)
        self.assertFalse(Station._authenticate("wrong-key"))
        self.assertFalse(Station._authenticate(False))

    def test_heartbeat_unauthorized(self):
        res = self._post("/tc/heartbeat", {}, key="bad")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(self.station.last_seen)

    def test_legacy_agent_key_header_refused(self):
        """Only ``X-Station-Key`` authenticates; the old ``X-Agent-Key`` header is gone."""
        res = self.url_open(
            "/tc/heartbeat",
            data=b"{}",
            headers={"Content-Type": "application/json", "X-Agent-Key": self.station.api_key},
        )
        self.assertEqual(res.status_code, 401)
        self.assertFalse(self.station.last_seen)

    def test_heartbeat_stores_metadata(self):
        res = self._post(
            "/tc/heartbeat",
            {"version": "1.3.5", "os": "macOS", "features": ["anaf", "fiscal"]},
            key=self.station.api_key,
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])
        self.station.invalidate_recordset()
        self.assertTrue(self.station.last_seen)
        self.assertEqual(self.station.tc_version, "1.3.5")
        self.assertEqual(self.station.os, "macOS")
        self.assertEqual(self.station.features, "anaf,fiscal")

    def test_heartbeat_returns_company_lang(self):
        """The agent takes its interface language from the station company's partner."""
        partner = self.station.company_id.partner_id
        self.env["res.lang"]._activate_lang("ro_RO")
        partner.lang = "ro_RO"
        res = self._post("/tc/heartbeat", {}, key=self.station.api_key)
        self.assertEqual(res.json()["lang"], "ro_RO")
        partner.lang = False
        res = self._post("/tc/heartbeat", {}, key=self.station.api_key)
        self.assertEqual(res.json()["lang"], "en_US", "no language on the company falls back to English")

    def test_heartbeat_stores_simulation(self):
        """The simulated devices are shown on the station, and cleared when the agent leaves simulation."""
        body = {"version": "1.6.24", "fiscal_driver": "simulated", "simulated": ["fiscal", "terminal:demo"]}
        self._post("/tc/heartbeat", body, key=self.station.api_key)
        self.station.invalidate_recordset()
        self.assertEqual(self.station.fiscal_driver, "simulated")
        self.assertEqual(self.station.simulated_devices, "fiscal,terminal:demo")
        self.assertTrue(self.station.is_simulated)
        self._post("/tc/heartbeat", {"fiscal_driver": "fiscalwire", "simulated": []}, key=self.station.api_key)
        self.station.invalidate_recordset()
        self.assertEqual(self.station.fiscal_driver, "fiscalwire")
        self.assertFalse(self.station.simulated_devices)
        self.assertFalse(self.station.is_simulated)
        # an older agent does not send the key: the stored state is kept
        self.station._touch({"version": "1.6.20"})
        self.assertEqual(self.station.fiscal_driver, "fiscalwire")

    def test_job_round_trip(self):
        """Enqueue → poll (claim) → result (done) full cycle through the controller."""
        job = self.station.action_ping()
        self.assertEqual(job.state, "pending")

        res = self._post("/tc/poll", {"limit": 10}, key=self.station.api_key)
        self.assertEqual(res.status_code, 200)
        polled = res.json()["jobs"]
        self.assertEqual([j["id"] for j in polled], [job.id])
        self.assertEqual(polled[0]["type"], "ping")
        job.invalidate_recordset()
        self.assertEqual(job.state, "claimed")
        self.assertTrue(job.claimed_at)

        res = self._post(
            "/tc/result",
            {"job_id": job.id, "status": "done", "result": "pong"},
            key=self.station.api_key,
        )
        self.assertEqual(res.status_code, 200)
        job.invalidate_recordset()
        self.assertEqual(job.state, "done")
        self.assertEqual(job.result, "pong")
        self.assertTrue(job.done_at)

    def test_job_result_error(self):
        job = self.station.action_ping()
        self._post("/tc/poll", {}, key=self.station.api_key)
        res = self._post(
            "/tc/result",
            {"job_id": job.id, "status": "error", "error": "boom"},
            key=self.station.api_key,
        )
        self.assertEqual(res.status_code, 200)
        job.invalidate_recordset()
        self.assertEqual(job.state, "error")
        self.assertEqual(job.error, "boom")

    def test_result_unknown_job(self):
        res = self._post("/tc/result", {"job_id": 999999, "status": "done"}, key=self.station.api_key)
        self.assertEqual(res.status_code, 404)

    def test_poll_only_own_station_jobs(self):
        other = self.env["deltatech.tc.station"].create({"name": "Other Station"})
        job_other = other.action_ping()
        res = self._post("/tc/poll", {"limit": 10}, key=self.station.api_key)
        self.assertNotIn(job_other.id, [j["id"] for j in res.json()["jobs"]])
        job_other.invalidate_recordset()
        self.assertEqual(job_other.state, "pending")
        self.assertEqual(job_other.station_id, other)

    def test_result_rejected_unless_claimed(self):
        job = self.station.action_ping()
        body = {"job_id": job.id, "status": "done", "result": "pong"}
        res = self._post("/tc/result", body, key=self.station.api_key)
        self.assertEqual(res.status_code, 409)
        self._post("/tc/poll", {}, key=self.station.api_key)
        self.assertEqual(self._post("/tc/result", body, key=self.station.api_key).status_code, 200)
        body["result"] = "forged"
        res = self._post("/tc/result", body, key=self.station.api_key)
        self.assertEqual(res.status_code, 409)
        job.invalidate_recordset()
        self.assertEqual(job.result, "pong")

    def test_bad_input(self):
        res = self._post("/tc/poll", {"limit": "abc"}, key=self.station.api_key)
        self.assertEqual(res.status_code, 200)
        res = self._post("/tc/result", {"job_id": "x"}, key=self.station.api_key)
        self.assertEqual(res.status_code, 400)

    def test_result_runs_callback_with_a_user_and_company(self):
        """``/tc/result`` is ``auth="none"``: the callback must not see an anonymous default env."""
        partner = self.env["res.partner"].create({"name": "Callback target"})
        Job = self.env["deltatech.tc.job"]
        with patch.object(type(partner), "_tc_test_store_default_env", _tc_store_default_env, create=True):
            job = Job._tc_enqueue_http(
                self.station, url="http://192.168.1.50/api/x", callback=(partner, "_tc_test_store_default_env")
            )
            Job._claim_for_station(self.station)
            res = self._post(
                "/tc/result",
                {"job_id": job.id, "status": "done", "result": json.dumps({"status": 200, "body": "{}"})},
                key=self.station.api_key,
            )
        self.assertEqual(res.status_code, 200)
        job.invalidate_recordset()
        partner.invalidate_recordset()
        self.assertEqual(job.state, "done", job.error)
        expected = f"{self.env.ref('base.user_root').id}:{self.station.company_id.id}"
        self.assertEqual(partner.ref, expected, "the callback ran with an anonymous default env")
