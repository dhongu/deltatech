# © 2026 Deltatech / Terrabit
# Regression test for QUEUE-003 (legacy /run_jobs route)
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestLegacyRunJobsRoute(HttpCase):
    def test_run_jobs_route_removed(self):
        """/run_jobs called an undefined runner and always failed with a server
        error; it is removed, the supported entry point is /api/v1/queue/process."""
        self.authenticate("admin", "admin")
        response = self.url_open("/run_jobs", data={"run": "1"})
        self.assertEqual(response.status_code, 404)
