import json
from unittest.mock import MagicMock, patch

from odoo.tests import HttpCase, tagged

GH_PATH = "odoo.addons.deltatech_tc.models.github_update.requests"


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

    def _get(self, path, key=None):
        headers = {}
        if key is not None:
            headers["X-Station-Key"] = key
        return self.url_open(path, headers=headers)

    def test_agent_version_requires_key(self):
        self.assertEqual(self._get("/tc/agent/version").status_code, 401)
        self.assertEqual(self._get("/tc/agent/version", key="bad").status_code, 401)

    def test_agent_version_proxies_github(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_tc.update_repo", "owner/repo")
        ICP.set_param("deltatech_tc.update_token", "ghp_test")
        resp = MagicMock(status_code=200)
        resp.json.return_value = {
            "tag_name": "v9.9.9",
            "body": "notes",
            "assets": [{"name": "terrabit-connect.jar", "url": "https://api.github.com/.../assets/1"}],
        }
        with patch(GH_PATH) as req:
            req.get.return_value = resp
            r = self._get("/tc/agent/version", key=self.station.api_key)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["version"], "9.9.9")

    def test_agent_download_proxies_asset(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_tc.update_repo", "owner/repo")
        ICP.set_param("deltatech_tc.update_token", "ghp_test")
        rel = MagicMock(status_code=200)
        rel.json.return_value = {
            "tag_name": "v9.9.9",
            "assets": [{"name": "terrabit-connect.jar", "url": "https://api.github.com/.../assets/1"}],
        }
        asset = MagicMock(status_code=200, content=b"PK\x03\x04 fake-jar")
        with patch(GH_PATH) as req:
            req.get.side_effect = [rel, asset]
            r = self._get("/tc/agent/download", key=self.station.api_key)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b"PK\x03\x04 fake-jar")

    def test_agent_version_not_configured(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_tc.update_repo", "")
        ICP.set_param("deltatech_tc.update_token", "")
        self.assertEqual(self._get("/tc/agent/version", key=self.station.api_key).status_code, 502)

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
