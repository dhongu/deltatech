# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestDeltatechSms(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create two sms with the same body to exercise grouping by body
        self.sms1 = self.env["sms.sms"].create(
            {
                "number": "+40111111111",
                "body": "Hello",
            }
        )
        self.sms2 = self.env["sms.sms"].create(
            {
                "number": "+40222222222",
                "body": "Hello",
            }
        )

    def _patch_send_batch(self, side_effect=None, results=None):
        """Patch SmsApi._send_sms_batch in the sms_sms module's namespace."""
        import importlib

        module = importlib.import_module("odoo.addons.deltatech_sms.models.sms_sms")
        if side_effect is not None:
            return patch.object(module.SmsApi, "_send_sms_batch", side_effect=side_effect)
        return patch.object(module.SmsApi, "_send_sms_batch", return_value=results or [])

    def test_send_success_and_error_handling(self):
        # Prepare mixed results: one success, one server_error
        results = [
            {"uuid": self.sms1.uuid, "state": "success"},
            {"uuid": self.sms2.uuid, "state": "server_error"},
        ]
        with self._patch_send_batch(results=results):
            # unlink_sent=True (default) -> success gets to_delete True
            # unlink_failed=False (default) -> errors are not deleted
            (self.sms1 | self.sms2)._send()
        s1 = self.sms1.sudo().browse(self.sms1.id)
        s2 = self.sms2.sudo().browse(self.sms2.id)
        self.assertNotEqual(s1.state, "error")
        self.assertTrue(s1.to_delete, "Sent SMS should be marked for deletion by default")
        self.assertEqual(s2.state, "error")
        self.assertFalse(s2.to_delete, "Failed SMS should not be deleted by default")

    def test_send_exception_marks_error_without_raising(self):
        with self._patch_send_batch(side_effect=Exception("boom")):
            (self.sms1 | self.sms2)._send(raise_exception=False)
        s1 = self.sms1.sudo().browse(self.sms1.id)
        s2 = self.sms2.sudo().browse(self.sms2.id)
        self.assertEqual(s1.state, "error")
        self.assertEqual(s2.state, "error")

    def test_smsapi_contact_iap_basic_mapping(self):
        # Build params similar to sms tools API
        params = {
            "messages": [
                {
                    "content": "Hi",
                    "numbers": [
                        {"number": "+401", "uuid": "u1"},
                        {"number": "+402", "uuid": "u2"},
                    ],
                }
            ]
        }

        import importlib

        SmsApi = importlib.import_module("odoo.addons.deltatech_sms.models.sms_api").SmsApi

        class FakeAccount:
            def sudo(self):
                return self

            def send_sms(self, number, content):
                if number == "+401":
                    return {"status": 200, "message": "OK"}
                return {"status": 500, "message": "ERR"}

        # Provide a fake env for SmsApi to avoid patching read-only model attributes
        class FakeIapModel:
            def get(self, _key):
                return FakeAccount()

        class FakeEnv(dict):
            def __getitem__(self, item):
                if item == "iap.account":
                    return FakeIapModel()
                return dict.__getitem__(self, item)

        api = SmsApi(self.env)
        api.env = FakeEnv()
        res = api._contact_iap("/dummy", params)
        # Expect two results with mapped states
        self.assertEqual(len(res), 2)
        states = {r["uuid"]: r["state"] for r in res}
        self.assertEqual(states["u1"], "success")
        self.assertEqual(states["u2"], "server_error")

    def test_iap_send_sms_4pay_success_and_unidecode(self):
        # Use a non-persisted record to avoid required fields on iap.account
        account = self.env["iap.account"].new(
            {
                "sms_provider": "4pay",
                "sms_secret": "sek",
                "sms_gateway": "GW1",
            }
        )

        # Fake response object for requests.get
        class Resp:
            def __init__(self, content):
                self.content = content

        import importlib

        iap_mod = importlib.import_module("odoo.addons.deltatech_sms.models.iap")
        with patch.object(iap_mod, "requests") as preq:
            # Make .get return OK
            preq.get.return_value = Resp(b"OK queued")
            res = account.send_sms("+401234", "Ăăîșț test")
            self.assertEqual(res.get("status"), 200)
            # Verify unidecoded text is sent to provider
            args, kwargs = preq.get.call_args
            self.assertIn("params", kwargs)
            sent_text = kwargs["params"].get("msg_text")
            # No diacritics should remain in provider payload
            self.assertNotIn("ă", sent_text.lower())
            self.assertNotIn("î", sent_text.lower())
            self.assertNotIn("ș", sent_text.lower())
            self.assertNotIn("ț", sent_text.lower())

    def test_iap_send_sms_4pay_error(self):
        account = self.env["iap.account"].new(
            {
                "sms_provider": "4pay",
                "sms_secret": "sek",
                "sms_gateway": "GW1",
            }
        )

        class Resp:
            def __init__(self, content):
                self.content = content

        import importlib

        iap_mod = importlib.import_module("odoo.addons.deltatech_sms.models.iap")
        with patch.object(iap_mod, "requests") as preq:
            preq.get.return_value = Resp(b"ERROR: no credits")
            res = account.send_sms("+401234", "Hello")
            self.assertEqual(res.get("status"), 500)
            self.assertIn("ERROR", res.get("message", ""))

    def test_iap_send_sms_wapi_success_and_payload(self):
        account = self.env["iap.account"].new(
            {
                "sms_provider": "wapi",
                "sms_secret": "sek",
                "sms_gateway": "DEV1",
            }
        )

        class Resp:
            def __init__(self, status, payload):
                self.status_code = status
                self._payload = payload

            def json(self):
                return self._payload

        import importlib

        iap_mod = importlib.import_module("odoo.addons.deltatech_sms.models.iap")
        with patch.object(iap_mod, "requests") as preq:
            payload = {"status": 200, "message": "OK"}
            preq.post.return_value = Resp(200, payload)
            res = account.send_sms("+40999", "Ăăîșț test")
            self.assertEqual(res.get("status"), 200)
            # Check payload sent in data
            args, kwargs = preq.post.call_args
            data = kwargs.get("data")
            self.assertEqual(data.get("device"), "DEV1")
            self.assertEqual(data.get("phone"), "+40999")
            # Unidecode applied
            self.assertNotIn("ă", data.get("message").lower())

    def test_iap_send_sms_wapi_error(self):
        account = self.env["iap.account"].new(
            {
                "sms_provider": "wapi",
                "sms_secret": "sek",
                "sms_gateway": "DEV1",
            }
        )

        class Resp:
            def __init__(self, status, content):
                self.status_code = status
                self.content = content

            def json(self):
                return {"status": self.status_code, "message": "ERR"}

        import importlib

        iap_mod = importlib.import_module("odoo.addons.deltatech_sms.models.iap")
        with patch.object(iap_mod, "requests") as preq:
            preq.post.return_value = Resp(500, b"fail")
            res = account.send_sms("+40999", "Hello")
            self.assertEqual(res.get("status"), 500)
            self.assertEqual(res.get("data"), False)
            self.assertEqual(res.get("message"), b"fail")
