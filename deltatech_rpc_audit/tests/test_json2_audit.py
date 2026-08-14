# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""The modern ``/json/2`` endpoint has to be audited like the legacy ones.

``/xmlrpc``, ``/xmlrpc/2`` and ``/jsonrpc`` are deprecated in Odoo 19, so every
integration will move to ``/json/2`` sooner or later. Auditing only the old
endpoints means the trail goes quiet exactly as that happens: the calls are still
served, they just stop being visible, and nothing fails to say so.
"""

import json

from odoo.tests import tagged
from odoo.tests.common import HttpCase

AUDIT_LOGGER = "odoo.rpc.audit"


@tagged("post_install", "-at_install")
class TestJson2Audit(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rpc_user = cls.env["res.users"].create(
            {
                "name": "Json2 Audit Client",
                "login": "json2-audit-client",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        # /json/2 authenticates with a bearer key, not with a password the way the
        # legacy services do, so the integration needs one before it can call at all.
        cls.api_key = (
            cls.env["res.users.apikeys"].with_user(cls.rpc_user).sudo()._generate("rpc", "json2 audit test", False)
        )

    def _call(self, model, method, payload=None):
        return self.url_open(
            f"/json/2/{model}/{method}",
            data=json.dumps(payload or {}),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

    def test_a_json2_call_is_audited(self):
        """The line carries who called, from where, and what -- as for the legacy endpoints."""
        with self.assertLogs(AUDIT_LOGGER, level="INFO") as logs:
            response = self._call("res.partner", "search_count", {"domain": []})

        self.assertEqual(response.status_code, 200, response.text)
        logged = "\n".join(logs.output)
        self.assertIn("model=res.partner", logged)
        self.assertIn("method=search_count", logged)
        self.assertIn(f"uid={self.rpc_user.id}", logged)
        self.assertIn("via=json2", logged)

    def test_the_arguments_are_logged(self):
        """Which records and which arguments is the reason to read the line at all."""
        partner = self.env["res.partner"].create({"name": "Json2 Audited Partner"})

        with self.assertLogs(AUDIT_LOGGER, level="INFO") as logs:
            response = self._call("res.partner", "read", {"ids": [partner.id], "fields": ["name"]})

        self.assertEqual(response.status_code, 200, response.text)
        logged = "\n".join(logs.output)
        self.assertIn(str(partner.id), logged)
        self.assertIn("name", logged)

    def test_the_platform_cron_poll_is_not_logged(self):
        """Odoo.sh drives the scheduler through this endpoint in a tight loop.

        Logging it would bury the handful of integration calls the audit exists for,
        so it is skipped by (model, method) -- the address it comes from is not stable
        enough to skip by IP.
        """
        from odoo.addons.deltatech_rpc_audit.controllers.rpc import _JSON2_SKIP

        self.assertIn(("ir.cron", "acquire_job"), _JSON2_SKIP)

    def test_the_legacy_line_format_is_unchanged(self):
        """Existing greps and log parsers key on these fields; only `via` is new."""
        with self.assertLogs(AUDIT_LOGGER, level="INFO") as logs:
            self._call("res.partner", "search_count", {"domain": []})

        line = next(m for m in logs.output if "via=json2" in m)
        for field in ("RPC ip=", "db=", "uid=", "model=", "method=", "args="):
            self.assertIn(field, line)
