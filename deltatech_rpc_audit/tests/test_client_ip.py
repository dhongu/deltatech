# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""The audited IP must not come from a header the caller controls.

The first entry of ``X-Forwarded-For`` is whatever the client sent -- nginx only
appends to it -- so trusting it let anyone with an API key pose as an address in
``ignore_ips`` and drop out of the audit.
"""

import json
import xmlrpc.client
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.deltatech_rpc_audit.controllers import rpc

AUDIT_LOGGER = "odoo.rpc.audit"
IGNORED_IP = "10.9.9.9"


@tagged("post_install", "-at_install")
class TestClientIp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rpc_user = cls.env["res.users"].create(
            {
                "name": "Spoofing Client",
                "login": "rpc-audit-spoofer",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.api_key = (
            cls.env["res.users.apikeys"].with_user(cls.rpc_user).sudo()._generate("rpc", "client ip test", False)
        )

    def _assert_logged_with_remote_addr(self, logs):
        logged = "\n".join(logs.output)
        self.assertNotIn(f"ip={IGNORED_IP}", logged)
        self.assertIn("ip=127.0.0.1", logged)
        # The header is kept as information, not as the IP.
        self.assertIn(f"xff='{IGNORED_IP}'", logged)

    def test_json2_spoofed_forwarded_for_is_still_logged(self):
        with patch.object(rpc, "_settings", return_value=(True, {IGNORED_IP})):
            with self.assertLogs(AUDIT_LOGGER, level="INFO") as logs:
                response = self.url_open(
                    "/json/2/res.partner/search_count",
                    data=json.dumps({"domain": []}),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                        "X-Forwarded-For": IGNORED_IP,
                    },
                )
        self.assertEqual(response.status_code, 200, response.text)
        self._assert_logged_with_remote_addr(logs)

    def test_xmlrpc_spoofed_forwarded_for_is_still_logged(self):
        payload = xmlrpc.client.dumps(
            (self.env.cr.dbname, self.rpc_user.id, self.api_key, "res.partner", "search_count", [[]]),
            "execute_kw",
        )
        with patch.object(rpc, "_settings", return_value=(True, {IGNORED_IP})):
            with self.assertLogs(AUDIT_LOGGER, level="INFO") as logs:
                response = self.url_open(
                    "/xmlrpc/2/object",
                    data=payload,
                    headers={"Content-Type": "text/xml", "X-Forwarded-For": IGNORED_IP},
                )
        self.assertEqual(response.status_code, 200, response.text)
        self._assert_logged_with_remote_addr(logs)

    def test_the_real_address_can_still_be_ignored(self):
        """``ignore_ips`` keeps working -- on the address the server resolved."""
        with patch.object(rpc, "_settings", return_value=(True, {"127.0.0.1"})):
            with self.assertNoLogs(AUDIT_LOGGER, level="INFO"):
                self.url_open(
                    "/json/2/res.partner/search_count",
                    data=json.dumps({"domain": []}),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                        "X-Forwarded-For": "203.0.113.7",
                    },
                )
