from odoo import Command
from odoo.tests import HttpCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestConfigDownload(HttpCase):
    """TC-001: /tc/config/<id> serves the API key only of a station the manager can read."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "TC-001 company B"})
        Station = cls.env["deltatech.tc.station"]
        cls.station_a = Station.create({"name": "TC-001 A", "company_id": cls.company_a.id})
        cls.station_b = Station.create({"name": "TC-001 B", "company_id": cls.company_b.id})
        cls.manager_a = new_test_user(
            cls.env,
            login="tc001_manager_a",
            groups="base.group_user,deltatech_tc.group_deltatech_tc_manager",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        cls.manager_ab = new_test_user(
            cls.env,
            login="tc001_manager_ab",
            groups="base.group_user,deltatech_tc.group_deltatech_tc_manager",
            company_id=cls.company_a.id,
            company_ids=[Command.set((cls.company_a | cls.company_b).ids)],
        )
        cls.internal = new_test_user(cls.env, login="tc001_internal", groups="base.group_user")

    def _download(self, login, station_id):
        self.authenticate(login, login)
        return self.url_open(f"/tc/config/{station_id}")

    def test_manager_downloads_own_company_station(self):
        res = self._download("tc001_manager_a", self.station_a.id)
        self.assertEqual(res.status_code, 200)
        self.assertIn(f"TERRABIT_STATION_KEY={self.station_a.api_key}", res.text)

    def test_manager_cannot_download_other_company_station(self):
        res = self._download("tc001_manager_a", self.station_b.id)
        self.assertEqual(res.status_code, 404)
        self.assertNotIn(self.station_b.api_key, res.text)

    def test_manager_with_both_companies(self):
        res = self._download("tc001_manager_ab", self.station_b.id)
        self.assertEqual(res.status_code, 200)
        self.assertIn(f"TERRABIT_STATION_KEY={self.station_b.api_key}", res.text)

    def test_internal_user_and_missing_station(self):
        res = self._download("tc001_internal", self.station_a.id)
        self.assertEqual(res.status_code, 404)
        self.assertNotIn(self.station_a.api_key, res.text)
        res = self._download("tc001_manager_a", self.station_b.id + 100000)
        self.assertEqual(res.status_code, 404)
