import json
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


def _tc_store_status(self, job):
    """Stand-in callback: records what came back, so the test can assert on it.

    Writes to `ref` (Char) rather than `comment` (Html), which would wrap it in <p>.
    """
    self.ref = str(job.response_dict().get("status"))


@tagged("post_install", "-at_install")
class TestTcHttp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.station = cls.env["deltatech.tc.station"].create({"name": "Test Station"})
        cls.Job = cls.env["deltatech.tc.job"]

    def _enqueue(self, **kw):
        kw.setdefault("url", "http://192.168.1.50/api/Lines")
        return self.Job._tc_enqueue_http(self.station, **kw)

    def _with_callback(self):
        """Attach the stand-in callback to res.partner for the duration of a test.

        Injected rather than shipped: a `_tc_` method in the module would be dead
        code, and using a real one would tie the test to another module.
        """
        return patch.object(type(self.env["res.partner"]), "_tc_test_store_status", _tc_store_status, create=True)

    # ------------------------------------------------------------------
    def test_enqueue_builds_payload(self):
        job = self._enqueue(headers={"X-API-KEY": "k"}, timeout=15)
        self.assertEqual(job.job_type, "http_request")
        self.assertEqual(job.state, "pending")
        self.assertEqual(job.station_id, self.station)
        payload = job.payload_dict()
        self.assertEqual(payload["url"], "http://192.168.1.50/api/Lines")
        self.assertEqual(payload["method"], "GET", "the method defaults to GET, upper-cased")
        self.assertEqual(payload["headers"], {"X-API-KEY": "k"})
        self.assertEqual(payload["timeout"], 15)

    def test_station_claims_the_job(self):
        job = self._enqueue()
        claimed = self.Job._claim_for_station(self.station)
        self.assertIn(job, claimed)
        self.assertEqual(job.state, "claimed")

    def test_rejects_unusable_requests(self):
        """Odoo validates the shape only — the host allow-list belongs to the agent."""
        with self.assertRaises(ValidationError):
            self._enqueue(url="ftp://192.168.1.50/x")
        with self.assertRaises(ValidationError):
            self._enqueue(url="not-a-url")
        with self.assertRaises(ValidationError):
            self._enqueue(method="TRACE")

    def test_response_helpers(self):
        job = self._enqueue()
        job._store_result(
            "done",
            result=json.dumps({"status": 200, "headers": {}, "body": '[{"line":"1"}]'}),
        )
        self.assertEqual(job.state, "done")
        self.assertEqual(job.response_dict()["status"], 200)
        self.assertEqual(job.response_json(), [{"line": "1"}])

    def test_response_helpers_survive_garbage(self):
        """A device that answers HTML must not raise — callers branch on status."""
        job = self._enqueue()
        job._store_result("done", result="<html>oops</html>")
        self.assertEqual(job.response_dict(), {})
        self.assertIsNone(job.response_json())

        other = self._enqueue()
        other._store_result("done", result=json.dumps({"status": 200, "body": "plain text"}))
        self.assertIsNone(other.response_json(), "a non-JSON body yields None, not an exception")

    def test_error_from_station_is_kept(self):
        job = self._enqueue()
        job._store_result("error", error="host not allowed")
        self.assertEqual(job.state, "error")
        self.assertEqual(job.error, "host not allowed")

    # ------------------------------------------------------------------
    # callbacks
    # ------------------------------------------------------------------
    def test_callback_runs_on_result(self):
        with self._with_callback():
            partner = self.env["res.partner"].create({"name": "Callback target"})
            job = self._enqueue(callback=(partner, "_tc_test_store_status"))
            self.assertEqual(job.callback_model, "res.partner")
            self.assertEqual(job.callback_res_id, partner.id)

            job._store_result("done", result=json.dumps({"status": 200, "body": '{"ok": true}'}))
            self.assertEqual(job.state, "done")
            self.assertEqual(partner.ref, "200")

    def test_callback_must_carry_the_prefix(self):
        """The method name lives in the database, so anything else is refused."""
        partner = self.env["res.partner"].create({"name": "Callback target"})
        with self.assertRaises(UserError):
            self._enqueue(callback=(partner, "unlink"))
        with self.assertRaises(UserError):
            self._enqueue(callback=(partner, "_tc_does_not_exist"))

    def test_tampered_callback_is_refused_at_call_time(self):
        with self._with_callback():
            partner = self.env["res.partner"].create({"name": "Callback target"})
            job = self._enqueue(callback=(partner, "_tc_test_store_status"))
            # bypass the constraint the way a direct SQL write or a broken migration would
            self.env.cr.execute("UPDATE deltatech_tc_job SET callback_method = 'unlink' WHERE id = %s", (job.id,))
            job.invalidate_recordset()
            job._store_result("done", result=json.dumps({"status": 200, "body": "{}"}))
            self.assertEqual(job.state, "error", "the job must fail instead of calling unlink")
            self.assertTrue(partner.exists(), "the target must still be there")

    def test_callback_target_deleted_meanwhile(self):
        with self._with_callback():
            partner = self.env["res.partner"].create({"name": "Gone by then"})
            job = self._enqueue(callback=(partner, "_tc_test_store_status"))
            partner.unlink()
            job._store_result("done", result=json.dumps({"status": 200, "body": "{}"}))
            self.assertEqual(job.state, "done", "a vanished target is skipped, not an error")

    def test_ping_still_works(self):
        """The base job type must be unaffected by this module."""
        job = self.Job.create({"station_id": self.station.id, "job_type": "ping"})
        job._store_result("done", result="pong")
        self.assertEqual(job.state, "done")
