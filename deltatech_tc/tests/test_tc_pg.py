import json
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import HttpCase, TransactionCase, tagged

_JOB_LOGGER = "odoo.addons.deltatech_tc.models.deltatech_tc_job"


def _tc_collect_page(self, job):
    """Stand-in page callback: appends what arrived to ``ref`` (Char), so the test can
    follow the chain. ``FAIL`` in the rows makes it raise, like a consumer that
    cannot process a page."""
    if job.state == "error":
        self.ref = f"{self.ref or ''}|error:{job.pg_error().get('code')}"
        return
    codes = [row["code"] for row in job.pg_rows()]
    if "FAIL" in codes:
        raise UserError(self.env._("cannot process this page"))
    self.ref = f"{self.ref or ''}|{job.payload_dict().get('page')}:{','.join(codes)}"


def _page(rows, more=False, next_key=None, page=0):
    return json.dumps(
        {
            "columns": [{"name": "code", "type": "text"}],
            "rows": [{"code": r} for r in rows],
            "count": len(rows),
            "more": more,
            "next": next_key,
            "page": page,
            "elapsed_ms": 3,
        }
    )


@tagged("post_install", "-at_install")
class TestTcPgQuery(TransactionCase):
    """``pg_query``: one page of a named query per job, chained by Odoo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.station = cls.env["deltatech.tc.station"].create({"name": "ERP server"})
        cls.Job = cls.env["deltatech.tc.job"]
        cls.partner = cls.env["res.partner"].create({"name": "Sync request"})

    def _with_callback(self):
        return patch.object(type(self.env["res.partner"]), "_tc_test_collect_page", _tc_collect_page, create=True)

    def _enqueue(self, **kw):
        kw.setdefault("params", {"since": "2026-11-01"})
        return self.Job._tc_enqueue_pg_query(self.station, "erp", "orders_since", **kw)

    def _answer(self, job, result=None, error=None):
        """What /tc/result does: the station claims the job, then reports."""
        if job.state == "pending":
            self.Job._claim_for_station(self.station)
        job._store_result(status="error" if error else "done", result=result, error=error)

    def _chain(self):
        return self.Job.search([("station_id", "=", self.station.id), ("job_type", "=", "pg_query")], order="id")

    # ------------------------------------------------------------------
    def test_enqueue_builds_payload(self):
        job = self._enqueue(page_size=500)
        self.assertEqual(job.job_type, "pg_query")
        self.assertEqual(job.state, "pending")
        self.assertEqual(
            job.payload_dict(),
            {
                "profile": "erp",
                "query": "orders_since",
                "params": {"since": "2026-11-01"},
                "after": None,
                "page": 0,
                "page_size": 500,
                "follow": True,
            },
        )
        self.assertTrue(job._tc_is_retry_safe(), "a page is a read: it may run again")

    def test_rejects_unusable_payloads(self):
        """Only names travel to the station - never SQL, never a path."""
        for profile, query in (("erp", "select * from x"), ("../etc", "q"), ("", "q"), ("erp", "a;b")):
            with self.assertRaises(ValidationError, msg=f"{profile}/{query}"):
                self.Job._tc_enqueue_pg_query(self.station, profile, query)
        with self.assertRaises(ValidationError):
            self._enqueue(page_size=0)
        with self.assertRaises(ValidationError):
            self._enqueue(page_size=50000)
        with self.assertRaises(ValidationError):
            self.Job.create(
                {
                    "station_id": self.station.id,
                    "job_type": "pg_query",
                    "payload": json.dumps({"profile": "w", "query": "q", "params": [1]}),
                }
            )
        with self.assertRaises(UserError):
            self.Job._tc_enqueue_pg_query(self.env["deltatech.tc.station"], "w", "q")
        with self.assertRaises(UserError):
            self._enqueue(callback=(self.partner, "unlink"))

    def test_pages_are_chained_until_the_last(self):
        with self._with_callback():
            first = self._enqueue(page_size=2, callback=(self.partner, "_tc_test_collect_page"))
            self._answer(first, _page(["A1", "A2"], more=True, next_key="A2"))
            chain = self._chain()
            self.assertEqual(len(chain), 2, "the next page is queued once the first is processed")
            second = chain[1]
            payload = second.payload_dict()
            self.assertEqual((payload["after"], payload["page"], payload["page_size"]), ("A2", 1, 2))
            self.assertEqual(payload["params"], {"since": "2026-11-01"})
            self.assertEqual(second.callback_method, "_tc_test_collect_page")
            self.assertEqual(second.callback_res_id, self.partner.id)
            self._answer(second, _page(["A3"], page=1))
        self.assertEqual(len(self._chain()), 2, "no page after more=false")
        self.assertEqual(self.partner.ref, "|0:A1,A2|1:A3")
        self.assertEqual(second.pg_rows(), [{"code": "A3"}])

    def test_sql_from_odoo_is_chained_with_its_key(self):
        sql = "SELECT code FROM erp.articles WHERE (%(after)s::text IS NULL OR code > %(after)s) ORDER BY code"
        first = self.Job._tc_enqueue_pg_query(self.station, "erp", sql=sql, key="code", page_size=2)
        payload = first.payload_dict()
        self.assertEqual((payload["sql"], payload["key"]), (sql, "code"))
        self.assertNotIn("query", payload, "the station must not look for a query file")
        self._answer(first, _page(["A1", "A2"], more=True, next_key="A2"))
        second = self._chain()[1].payload_dict()
        self.assertEqual((second["sql"], second["key"], second["after"], second["page"]), (sql, "code", "A2", 1))

    def test_sql_or_query_but_not_both(self):
        with self.assertRaises(UserError):
            self.Job._tc_enqueue_pg_query(self.station, "erp")
        with self.assertRaises(UserError):
            self.Job._tc_enqueue_pg_query(self.station, "erp", "orders_since", sql="SELECT 1")
        with self.assertRaises(ValidationError):
            self.Job._tc_enqueue_pg_query(self.station, "erp", sql="SELECT 1", key="cod mag")
        with self.assertRaises(ValidationError):
            self.Job._tc_enqueue_pg_query(self.station, "erp", sql="SELECT '" + "x" * 100001 + "'")
        with self.assertRaises(ValidationError):
            self.Job._tc_enqueue_pg_query(self.station, "bad profile", sql="SELECT 1")
        job = self.Job._tc_enqueue_pg_query(self.station, "erp", sql="SELECT 1 AS x")
        self.assertIsNone(job.payload_dict()["key"], "one page, no pagination key")

    def test_no_follow_stops_after_one_page(self):
        job = self._enqueue(follow=False)
        self._answer(job, _page(["A1"], more=True, next_key="A1"))
        self.assertEqual(len(self._chain()), 1)

    def test_failing_callback_stops_the_chain(self):
        with self._with_callback(), self.assertLogs(_JOB_LOGGER, level="ERROR"):
            job = self._enqueue(callback=(self.partner, "_tc_test_collect_page"))
            self._answer(job, _page(["FAIL"], more=True, next_key="FAIL"))
        self.assertEqual(job.state, "error")
        self.assertIn("cannot process this page", job.error)
        self.assertEqual(len(self._chain()), 1, "a page that could not be processed is not skipped")
        job.action_retry()
        self.assertEqual(job.state, "pending", "Retry takes the chain up from the same page")

    def test_more_without_key_is_an_error(self):
        with self.assertLogs(_JOB_LOGGER, level="ERROR"):
            job = self._enqueue()
            self._answer(job, _page(["A1"], more=True, next_key=None))
        self.assertEqual(job.state, "error")
        self.assertEqual(len(self._chain()), 1)

    def test_station_error_reaches_the_callback(self):
        with self._with_callback():
            job = self._enqueue(callback=(self.partner, "_tc_test_collect_page"))
            self._answer(job, error=json.dumps({"code": "undefined_table", "message": "elemente_2019 missing"}))
        self.assertEqual(job.state, "error")
        self.assertEqual(job.pg_error()["code"], "undefined_table")
        self.assertEqual(self.partner.ref, "|error:undefined_table")
        self.assertEqual(len(self._chain()), 1)

    def test_plain_text_error(self):
        job = self._enqueue()
        self._answer(job, error="station crashed")
        self.assertEqual(job.pg_error(), {"code": "error", "message": "station crashed"})
        self.assertEqual(self.Job.browse().new({"job_type": "pg_query"}).pg_error(), {})

    def test_lost_page_is_offered_again_then_failed(self):
        self.env["ir.config_parameter"].sudo().set_str("deltatech_tc.max_attempts", "2")
        with self._with_callback():
            job = self._enqueue(callback=(self.partner, "_tc_test_collect_page"))
            for attempt in (1, 2):
                self.Job._claim_for_station(self.station)
                self.assertEqual((job.state, job.attempt_count), ("claimed", attempt))
                job.write({"claimed_at": fields.Datetime.now() - timedelta(minutes=16)})
            self.Job._requeue_lost_jobs(self.station)
        self.assertEqual(job.state, "error")
        self.assertEqual(self.partner.ref, "|error:error", "the waiting record learns about the failure")

    def test_chain_stops_when_the_callback_target_is_gone(self):
        partner = self.env["res.partner"].create({"name": "Short-lived request"})
        with self._with_callback():
            job = self.Job._tc_enqueue_pg_query(
                self.station, "erp", "articles", callback=(partner, "_tc_test_collect_page")
            )
            partner.unlink()
            with self.assertLogs(_JOB_LOGGER, level="WARNING"):
                self._answer(job, _page(["A1"], more=True, next_key="A1"))
        self.assertEqual(job.state, "done")
        self.assertEqual(len(self._chain()), 1)

    def test_gc_drops_old_pages_sooner(self):
        now = fields.Datetime.now()
        page = self._enqueue()
        page.write({"state": "done", "done_at": now - timedelta(hours=7), "result": _page(["A1"])})
        fresh = self._enqueue()
        fresh.write({"state": "done", "done_at": now - timedelta(hours=2), "result": _page(["A2"])})
        ping = self.Job.create({"station_id": self.station.id, "job_type": "ping"})
        ping.write({"state": "done", "done_at": now - timedelta(days=5)})
        self.Job._gc_jobs()
        self.assertFalse(page.exists(), "pg_query pages go after 6 hours")
        self.assertTrue(fresh.exists(), "a page processed 2 hours ago is kept")
        self.assertTrue(ping.exists(), "other jobs keep the 30-day retention")

    def test_gc_pages_legacy_days_param(self):
        """``pg_done_ttl_days`` (before the hours) still counts when only it is set."""
        self.env["ir.config_parameter"].sudo().set_int("deltatech_tc.pg_done_ttl_days", 1)
        page = self._enqueue()
        page.write({"state": "done", "done_at": fields.Datetime.now() - timedelta(hours=7)})
        self.Job._gc_jobs()
        self.assertTrue(page.exists(), "1 day, not 6 hours")

    def test_gc_pages_legacy_days_zero_keeps_them(self):
        """``pg_done_ttl_days = 0`` meant no early deletion: the pages follow the other jobs."""
        self.env["ir.config_parameter"].sudo().set_str("deltatech_tc.pg_done_ttl_days", "0")
        page = self._enqueue()
        page.write({"state": "done", "done_at": fields.Datetime.now() - timedelta(days=2)})
        self.Job._gc_jobs()
        self.assertTrue(page.exists(), "0 turns the early deletion off, not 6 hours")


@tagged("post_install", "-at_install")
class TestTcPgStation(HttpCase):
    """What the Terrabit Connect PostgreSQL agent reports, and how a module finds it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Station = cls.env["deltatech.tc.station"]
        cls.station = cls.Station.create({"name": "ERP server"})

    def _heartbeat(self, body):
        res = self.url_open(
            "/tc/heartbeat",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "X-Station-Key": self.station.api_key},
        )
        self.assertEqual(res.status_code, 200)
        self.station.invalidate_recordset()

    def test_heartbeat_stores_capabilities(self):
        self._heartbeat(
            {
                "version": "0.1.0",
                "os": "windows",
                "agent": "tc-postgresql",
                "features": ["postgresql", "pg:erp", "pg_sql:erp"],
                "pg_profiles": {"erp": ["orders_since", "articles"], "bad": "not a list"},
            }
        )
        self.assertEqual(self.station.agent_name, "tc-postgresql")
        self.assertEqual(self.station.features, "postgresql,pg:erp,pg_sql:erp")
        self.assertTrue(self.station._tc_has_pg_sql("erp"))
        self.assertFalse(self.station._tc_has_pg_sql("bad"), "SQL is allowed per profile")
        self.assertEqual(self.station.capabilities, {"erp": ["orders_since", "articles"], "bad": []})
        self.assertIn("erp: orders_since, articles", self.station.capabilities_display)
        self.assertIn(
            "bad", self.station.capabilities_display.splitlines(), "a profile without query files shows its name"
        )
        self.assertTrue(self.station._tc_has_pg_query("erp", "articles"))
        self.assertFalse(self.station._tc_has_pg_query("erp", "clients"))
        self.assertFalse(self.station._tc_has_pg_query("other", "articles"))
        # the desktop app sends no pg_profiles: what is stored stays
        self._heartbeat({"version": "0.1.1"})
        self.assertTrue(self.station._tc_has_pg_query("erp", "articles"))
        self._heartbeat({"pg_profiles": {}})
        self.assertFalse(self.station.capabilities)
        self.assertFalse(self.station.capabilities_display)

    def test_find_station_by_whole_feature(self):
        self.station.sudo().write({"features": "postgresql,pg:erp_test"})
        self.assertFalse(self.Station._tc_find("pg:erp"), "a prefix is not a match")
        other = self.Station.create({"name": "Second", "features": "postgresql,pg:erp"})
        self.assertEqual(self.Station._tc_find("pg:erp"), other)
        other.active = False
        self.assertFalse(self.Station._tc_find("pg:erp"), "archived stations are skipped")
        company = self.env["res.company"].create({"name": "Elsewhere"})
        self.assertFalse(self.Station._tc_find("pg:erp_test", company=company), "only the company's stations")
