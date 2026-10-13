# © 2026 Terrabit / Contributors
# CATEGORYGROUP-001: grupul de manager se dă utilizatorilor, nu implică id-uri de utilizatori ca grupuri

import importlib.util

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import SQL, file_path


@tagged("post_install", "-at_install")
class TestCategoryGroupManager(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = cls.env.ref("deltatech_category_group.category_group_manager")
        cls.user_root = cls.env.ref("base.user_root")
        cls.user_admin = cls.env.ref("base.user_admin")

    def test_group_implies_no_groups(self):
        # modulul nu declară nicio implicare; vechiul XML punea aici id-urile utilizatorilor
        self.assertFalse(self.group.implied_ids)

    def test_admin_users_are_members(self):
        self.assertIn(self.user_root, self.group.with_context(active_test=False).user_ids)
        self.assertIn(self.user_admin, self.group.user_ids)
        self.assertTrue(self.user_admin.has_group("deltatech_category_group.category_group_manager"))

    def _implied_hids(self):
        self.env.cr.execute(
            SQL("SELECT hid FROM res_groups_implied_rel WHERE gid = %s", self.group.id),
        )
        return {row[0] for row in self.env.cr.fetchall()}

    def test_migration_removes_only_wrong_links(self):
        wrong_ids = {self.user_root.id, self.user_admin.id}
        legit = self.env["res.groups"].search([("id", "not in", list(wrong_ids))], limit=1)
        wrong_groups = self.env["res.groups"].browse(list(wrong_ids)).exists()
        # simulează o bază instalată cu vechiul XML + o implicare adăugată manual
        for hid in wrong_groups.ids + legit.ids:
            self.env.cr.execute(
                SQL(
                    "INSERT INTO res_groups_implied_rel (gid, hid) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    self.group.id,
                    hid,
                )
            )
        self.assertEqual(self._implied_hids(), set(wrong_groups.ids) | set(legit.ids))

        path = file_path("deltatech_category_group/migrations/19.0.0.0.6/post-migration.py")
        spec = importlib.util.spec_from_file_location("deltatech_category_group_mig_19_0_0_0_6", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        migration.migrate(self.env.cr, "19.0.0.0.5")

        self.assertEqual(self._implied_hids(), set(legit.ids))
