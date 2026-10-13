# © 2026 Deltatech / Terrabit
# Regression tests for TRANSPORT-001 / TRANSPORT-002
import os
import shutil
import tempfile

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTransportSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo = cls.env["transport.repo"].create(
            {
                "name": "Secured Repo",
                "module_name": "my_module",
                "repo_url": "https://example.com/org/repo.git",
                "repo_branch": "main",
                "credential_type": "https",
                "username": "deploy",
                "password": "s3cr3t-token",
            }
        )
        cls.config = cls.env["transport.config"].create(
            {
                "name": "Partners",
                "model_id": cls.env.ref("base.model_res_partner_category").id,
                "repo_id": cls.repo.id,
            }
        )
        cls.user = new_test_user(cls.env, login="transport_internal", groups="base.group_user")
        cls.admin = new_test_user(cls.env, login="transport_admin", groups="base.group_user,base.group_system")

    def setUp(self):
        super().setUp()
        self.parent = tempfile.mkdtemp(prefix="odoo_transport_sec_")
        self.root = os.path.join(self.parent, "clone")
        module_root = os.path.join(self.root, "my_module")
        os.makedirs(module_root)
        with open(os.path.join(module_root, "__manifest__.py"), "w", encoding="utf-8") as f:
            f.write('{"name": "My Module", "version": "19.0.0.0.1", "data": []}\n')

    def tearDown(self):
        shutil.rmtree(self.parent, ignore_errors=True)
        super().tearDown()

    # TRANSPORT-001
    def test_internal_user_cannot_read_repo_credentials(self):
        repo = self.repo.with_user(self.user)
        with self.assertRaises(AccessError):
            repo.read(["password"])
        with self.assertRaises(AccessError):
            repo.read(["name"])
        with self.assertRaises(AccessError):
            repo.write({"repo_branch": "evil"})
        with self.assertRaises(AccessError):
            self.env["transport.repo"].with_user(self.user).create(
                {"name": "x", "module_name": "x", "repo_url": "https://e.com/x.git", "repo_branch": "main"}
            )

    def test_internal_user_cannot_export(self):
        with self.assertRaises(AccessError):
            self.config.with_user(self.user).action_export_csv()
        with self.assertRaises(AccessError):
            self.config.with_user(self.user).read(["name"])

    def test_admin_keeps_access(self):
        repo = self.repo.with_user(self.admin)
        self.assertEqual(repo.read(["password"])[0]["password"], "s3cr3t-token")
        repo.write({"repo_branch": "dev"})
        self.assertEqual(self.config.with_user(self.admin).name, "Partners")

    def test_repo_operations_are_private(self):
        for name in ("clone_to_temp", "write_csv_and_update_manifest", "commit_and_push"):
            self.assertFalse(hasattr(self.repo, name), name)

    def test_internal_user_cannot_call_writer(self):
        with self.assertRaises(AccessError):
            self.repo.with_user(self.user)._write_csv_and_update_manifest(self.root, "a.csv", "id\n")

    # TRANSPORT-002
    def test_module_name_traversal_rejected_on_save(self):
        for bad in ("../outside", "/tmp/x", "a/b", "..", ""):
            with self.assertRaises(ValidationError, msg=bad):
                self.repo.write({"module_name": bad})

    def test_module_name_traversal_writes_nothing(self):
        # bypass the constraint, as an existing record stored before the fix would
        self.env.cr.execute("UPDATE transport_repo SET module_name = '../outside' WHERE id = %s", [self.repo.id])
        self.repo.invalidate_recordset(["module_name"])
        os.makedirs(os.path.join(self.parent, "outside"))
        with open(os.path.join(self.parent, "outside", "__manifest__.py"), "w", encoding="utf-8") as f:
            f.write('{"name": "Outside", "data": []}\n')
        with self.assertRaises(UserError):
            self.repo._write_csv_and_update_manifest(self.root, "a.csv", "payload")
        self.assertFalse(os.path.exists(os.path.join(self.parent, "outside", "data")))

    def test_symlink_escape_rejected(self):
        outside = os.path.join(self.parent, "outside")
        os.makedirs(outside)
        os.symlink(outside, os.path.join(self.root, "my_module", "data"))
        with self.assertRaises(UserError):
            self.repo._write_csv_and_update_manifest(self.root, "a.csv", "payload")
        self.assertFalse(os.listdir(outside))

    def test_missing_manifest_has_no_side_effect(self):
        os.remove(os.path.join(self.root, "my_module", "__manifest__.py"))
        with self.assertRaises(UserError):
            self.repo._write_csv_and_update_manifest(self.root, "a.csv", "payload")
        self.assertFalse(os.path.exists(os.path.join(self.root, "my_module", "data")))

    def test_valid_write_still_works(self):
        csv_path, _manifest, changed, rel = self.repo._write_csv_and_update_manifest(self.root, "a.csv", "id\n")
        self.assertTrue(os.path.isfile(csv_path))
        self.assertTrue(changed)
        self.assertEqual(rel, os.path.join("data", "a.csv"))
