# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, tagged

POST = "odoo.addons.deltatech_website_indexnow.models.website.requests.post"
KEY = "9c42dc26ca5946e4b661082db126af42"


@tagged("post_install", "-at_install")
class TestIndexNow(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].browse(1)
        cls.website.domain = "https://www.example.ro"

    def _create_page(self, url, published=True):
        view = self.env["ir.ui.view"].create(
            {"name": url, "type": "qweb", "arch": "<t><div/></t>", "key": f"test.{url.strip('/')}"}
        )
        return self.env["website.page"].create(
            {"url": url, "view_id": view.id, "website_id": self.website.id, "is_published": published}
        )

    def test_enable_generates_key(self):
        self.assertFalse(self.website.indexnow_key)
        self.website.indexnow_enabled = True
        self.assertRegex(self.website.indexnow_key, r"^[0-9a-f]{32}$")
        self.assertTrue(self.website.indexnow_last_submit)
        self.assertEqual(self.website.indexnow_key_url, f"https://www.example.ro/{self.website.indexnow_key}.txt")
        # a key typed by hand is kept
        other = self.env["website"].create({"name": "Other", "indexnow_enabled": True, "indexnow_key": KEY})
        self.assertEqual(other.indexnow_key, KEY)
        # an emptied key is generated again
        other.indexnow_key = False
        self.assertRegex(other.indexnow_key, r"^[0-9a-f]{32}$")

    def test_key_format(self):
        with self.assertRaises(ValidationError):
            self.website.indexnow_key = "short"
        with self.assertRaises(ValidationError):
            self.website.indexnow_key = "key with spaces"

    def test_key_file(self):
        self.website.write({"domain": False, "indexnow_enabled": True, "indexnow_key": KEY})
        response = self.url_open(f"/{KEY}.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, KEY)
        self.assertTrue(response.headers["Content-Type"].startswith("text/plain"))
        self.assertEqual(self.url_open("/0000000000000000.txt").status_code, 404)
        self.website.indexnow_enabled = False
        self.assertEqual(self.url_open(f"/{KEY}.txt").status_code, 404)

    def test_changed_urls(self):
        old = self._create_page("/indexnow-old")
        draft = self._create_page("/indexnow-draft", published=False)
        since = fields.Datetime.now()
        self.env.cr.execute(
            "UPDATE website_page SET write_date = %s WHERE id = %s", (since - timedelta(days=1), old.id)
        )
        self.env.cr.execute(
            "UPDATE ir_ui_view SET write_date = %s WHERE id = %s", (since - timedelta(days=1), old.view_id.id)
        )
        old.invalidate_recordset(["write_date"])
        old.view_id.invalidate_recordset(["write_date"])
        new = self._create_page("/indexnow-new")
        self.env.cr.execute(
            "UPDATE website_page SET write_date = %s WHERE id = %s", (since + timedelta(seconds=1), new.id)
        )
        new.invalidate_recordset(["write_date"])

        changed = self.website._indexnow_get_urls(since=since)
        self.assertIn("https://www.example.ro/indexnow-new", changed)
        self.assertNotIn("https://www.example.ro/indexnow-old", changed)
        self.assertNotIn("https://www.example.ro" + draft.url, changed)

        # the content edited in the website builder is written on the view of the page
        self.env.cr.execute(
            "UPDATE ir_ui_view SET write_date = %s WHERE id = %s", (since + timedelta(seconds=1), old.view_id.id)
        )
        old.view_id.invalidate_recordset(["write_date"])
        self.assertIn("https://www.example.ro/indexnow-old", self.website._indexnow_get_urls(since=since))

        everything = self.website._indexnow_get_urls()
        self.assertIn("https://www.example.ro/indexnow-old", everything)
        self.assertEqual(len(everything), len(set(everything)))

    def test_submit(self):
        self.website.write({"indexnow_enabled": True, "indexnow_key": KEY})
        self._create_page("/indexnow-sent")
        with patch(POST, return_value=MagicMock(status_code=202)) as post:
            action = self.website.action_indexnow_submit_all()
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["host"], "www.example.ro")
        self.assertEqual(payload["key"], KEY)
        self.assertEqual(payload["keyLocation"], f"https://www.example.ro/{KEY}.txt")
        self.assertIn("https://www.example.ro/indexnow-sent", payload["urlList"])
        self.assertEqual(action["params"]["type"], "success")
        self.assertIn("URLs sent", self.website.indexnow_last_result)

        # nothing changed since: nothing is sent
        with patch(POST) as post:
            self.env["website"]._cron_indexnow()
        post.assert_not_called()
        self.assertIn("Nothing to send", self.website.indexnow_last_result)

    def test_submit_error(self):
        self.website.write({"indexnow_enabled": True, "indexnow_key": KEY})
        last_submit = fields.Datetime.now() - timedelta(days=1)
        self.website.indexnow_last_submit = last_submit
        self._create_page("/indexnow-refused")
        with patch(POST, return_value=MagicMock(status_code=403, text="")):
            self.env["website"]._cron_indexnow()
        self.assertIn("HTTP 403", self.website.indexnow_last_result)
        # the same pages are sent again at the next run
        self.assertEqual(self.website.indexnow_last_submit, last_submit)

    def test_published_models(self):
        models = self.website._indexnow_published_models()
        self.assertIn("website.controller.page", models)
        self.assertNotIn("website.page", models)
        # published, but without a page of their own
        self.assertNotIn("website.checkout.step", models)
        self.assertNotIn("website.snippet.filter", models)

    def test_settings(self):
        settings = self.env["res.config.settings"].create({"website_id": self.website.id, "indexnow_enabled": True})
        settings.execute()
        self.assertTrue(self.website.indexnow_enabled)
        self.assertTrue(self.website.indexnow_key)
