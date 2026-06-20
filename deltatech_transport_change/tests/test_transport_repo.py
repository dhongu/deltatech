# © 2025 Deltatech / Terrabit
# Tests for TransportRepo model

import os
import tempfile

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestCredentializedUrl(TransactionCase):
    def _make_repo(self, **extra):
        vals = {
            "name": "Test Repo",
            "module_name": "my_module",
            "repo_url": "https://github.com/org/repo.git",
            "repo_branch": "main",
            "credential_type": "https",
            "username": "user",
            "password": "secret",
        }
        vals.update(extra)
        return self.env["transport.repo"].create(vals)

    def test_credentialized_url_basic(self):
        repo = self._make_repo()
        url = repo._credentialized_url("https://github.com/org/repo.git")
        self.assertIn("user:secret@", url)
        self.assertIn("github.com", url)

    def test_credentialized_url_special_chars_encoded(self):
        repo = self._make_repo(username="us/er", password="p@ss!")
        url = repo._credentialized_url("https://github.com/org/repo.git")
        self.assertNotIn("/", url.split("@")[0].split("//")[1].split(":")[0])
        self.assertIn("@github.com", url)

    def test_credentialized_url_raises_for_ssh(self):
        repo = self._make_repo()
        with self.assertRaises(UserError):
            repo._credentialized_url("git@github.com:org/repo.git")

    def test_credentialized_url_raises_for_git_scheme(self):
        repo = self._make_repo()
        with self.assertRaises(UserError):
            repo._credentialized_url("git://github.com/org/repo.git")


class TestWriteCsvAndUpdateManifest(TransactionCase):
    def setUp(self):
        super().setUp()
        self.repo_rec = self.env["transport.repo"].create(
            {
                "name": "Test Repo",
                "module_name": "my_module",
                "repo_url": "https://example.com/org/repo.git",
                "repo_branch": "main",
                "credential_type": "https",
                "username": "user",
                "password": "token",
            }
        )
        self.tmp = tempfile.mkdtemp()
        # Create module structure
        self.module_root = os.path.join(self.tmp, "my_module")
        os.makedirs(os.path.join(self.module_root, "data"), exist_ok=True)
        manifest_path = os.path.join(self.module_root, "__manifest__.py")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write('{"name": "My Module", "version": "19.0.0.0.1", "data": []}\n')

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)
        super().tearDown()

    def test_csv_written_to_data_dir(self):
        csv_content = "id,name\nbase.cat1,Cat 1\n"
        csv_path, _, _, rel_path = self.repo_rec.write_csv_and_update_manifest(
            self.tmp, "res.partner.category.csv", csv_content
        )
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, encoding="utf-8") as f:
            self.assertEqual(f.read(), csv_content)

    def test_manifest_updated_with_data_path(self):
        csv_content = "id,name\n"
        _, manifest_path, changed, rel_path = self.repo_rec.write_csv_and_update_manifest(
            self.tmp, "res.partner.category.csv", csv_content
        )
        self.assertTrue(changed)
        with open(manifest_path, encoding="utf-8") as f:
            manifest_txt = f.read()
        self.assertIn(rel_path, manifest_txt)

    def test_manifest_not_changed_if_already_present(self):
        # Pre-populate manifest with the path
        manifest_path = os.path.join(self.module_root, "__manifest__.py")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write('{"name": "My Module", "version": "19.0.0.0.1", "data": ["data/res.partner.category.csv"]}\n')
        _, _, changed, _ = self.repo_rec.write_csv_and_update_manifest(
            self.tmp, "res.partner.category.csv", "id,name\n"
        )
        self.assertFalse(changed)

    def test_invalid_filename_raises(self):
        with self.assertRaises(UserError):
            self.repo_rec.write_csv_and_update_manifest(self.tmp, "../../../etc/passwd", "data")

    def test_missing_manifest_raises(self):
        import shutil

        shutil.rmtree(self.module_root)
        os.makedirs(os.path.join(self.module_root, "data"))
        with self.assertRaises(UserError):
            self.repo_rec.write_csv_and_update_manifest(self.tmp, "test.csv", "id\n")


class TestEnsureManifestHasData(TransactionCase):
    def setUp(self):
        super().setUp()
        self.repo_rec = self.env["transport.repo"].create(
            {
                "name": "Manifest Test Repo",
                "module_name": "test_mod",
                "repo_url": "https://example.com/repo.git",
                "repo_branch": "main",
                "credential_type": "https",
                "username": "u",
                "password": "p",
            }
        )
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)
        super().tearDown()

    def _write_manifest(self, content):
        path = os.path.join(self.tmp, "__manifest__.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_adds_missing_entry(self):
        self._write_manifest('{"name": "X", "version": "19.0.0.0.1", "data": []}\n')
        _, changed = self.repo_rec._ensure_manifest_has_data_at(self.tmp, "data/foo.csv")
        self.assertTrue(changed)
        with open(os.path.join(self.tmp, "__manifest__.py"), encoding="utf-8") as f:
            txt = f.read()
        self.assertIn("data/foo.csv", txt)

    def test_no_change_if_entry_exists(self):
        self._write_manifest('{"name": "X", "version": "19.0.0.0.1", "data": ["data/foo.csv"]}\n')
        _, changed = self.repo_rec._ensure_manifest_has_data_at(self.tmp, "data/foo.csv")
        self.assertFalse(changed)

    def test_missing_manifest_raises(self):
        with self.assertRaises(UserError):
            self.repo_rec._ensure_manifest_has_data_at(self.tmp, "data/foo.csv")

    def test_invalid_manifest_raises(self):
        self._write_manifest("not_a_dict = 123\n")
        with self.assertRaises(UserError):
            self.repo_rec._ensure_manifest_has_data_at(self.tmp, "data/foo.csv")
