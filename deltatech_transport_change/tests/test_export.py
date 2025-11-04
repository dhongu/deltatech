# © 2025 Deltatech / Terrabit
# Standard Odoo test for deltatech_transport_change

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from odoo.tests.common import TransactionCase

try:
    import git  # GitPython
except Exception:  # pragma: no cover
    git = None


class TestTransportExport(TransactionCase):
    @unittest.skipIf(git is None, "GitPython not installed; skip Git-related tests")
    def setUp(self):  # noqa: D401
        super().setUp()
        # Prepare HTTPS token-based repo configuration (dummy URL; we won't actually push)
        self.module_name = "deltatech_test"
        self.target_branch = "test_branch"
        self.repo_rec = self.env["transport.repo"].create(
            {
                "name": "Test Repo",
                "module_name": self.module_name,
                "repo_url": "https://example.com/org/repo.git",
                "repo_branch": self.target_branch,
                "credential_type": "https",
                "username": "user",
                "password": "token",
            }
        )

        # Prepare a simple dataset to export: use res.partner.category with only 'name' field
        model = self.env["ir.model"].search([("model", "=", "res.partner.category")], limit=1)
        self.assertTrue(model, "Model res.partner.category should exist")
        name_field = self.env["ir.model.fields"].search([("model_id", "=", model.id), ("name", "=", "name")], limit=1)
        self.assertTrue(name_field, "Field 'name' must exist on res.partner.category")

        # Create a couple of categories (no xmlid, so fallback model,id will be used)
        self.env["res.partner.category"].create({"name": "Test Cat A"})
        self.env["res.partner.category"].create({"name": "Test Cat B"})

        # Create the transport config
        self.cfg = self.env["transport.config"].create(
            {
                "name": "Test Export Categories",
                "model_id": model.id,
                "field_ids": [(6, 0, [name_field.id])],
                "domain": "[]",
                "repo_id": self.repo_rec.id,
            }
        )

        # ===== Test repo and module path setup (temp clone simulation) =====
        self._orig_rmtree = shutil.rmtree
        self.temp_dir = tempfile.mkdtemp(prefix="odoo_transport_test_")

        # Prevent export cleanup from removing our temp dir; keep other deletions intact
        def _no_rmtree(path, *args, **kwargs):
            abs_path = os.path.abspath(path)
            if abs_path in (os.path.abspath(self.temp_dir), os.path.abspath(self.module_path)):
                return
            return self._orig_rmtree(path, *args, **kwargs)

        shutil.rmtree = _no_rmtree
        # Create module structure inside temp dir
        self.module_path = os.path.join(self.temp_dir, self.module_name)
        os.makedirs(os.path.join(self.module_path, "data"), exist_ok=True)
        # Minimal manifest
        manifest_path = os.path.join(self.module_path, "__manifest__.py")
        with open(manifest_path, "w", encoding="utf-8") as mf:
            mf.write("""
{
    "name":
    "Test",
    "version": "19.0.0.0.1",
    "data": [],
}
        """)
        # Init a git repo at temp root (as clone root), commit initial state, and create/checkout target branch
        self.repo = git.Repo.init(self.temp_dir)
        self.repo.git.add(A=True)
        self.repo.index.commit("init test repo")
        # create branch if not exists
        if self.target_branch not in [h.name for h in self.repo.heads]:
            self.repo.create_head(self.target_branch)
        self.repo.git.checkout(self.target_branch)

        # Patch clone_to_temp on TransportRepo to return our temp repo and commit_and_push to be local only
        # Patch clone_to_temp and commit_and_push using dotted path targets (avoid importing the model class here)
        self.clone_patcher = patch(
            "odoo.addons.deltatech_transport_change.models.transport_repo.TransportRepo.clone_to_temp",
            autospec=True,
            return_value=(self.temp_dir, self.repo),
        )
        self.clone_patcher.start()

        def _local_commit_and_push(self_repo, repo_obj, commit_message):
            repo_obj.git.add(A=True)
            if repo_obj.is_dirty(index=True, working_tree=True, untracked_files=True):
                repo_obj.index.commit(commit_message)
            # no push in tests

        self.commit_patcher = patch(
            "odoo.addons.deltatech_transport_change.models.transport_repo.TransportRepo.commit_and_push",
            autospec=True,
            side_effect=_local_commit_and_push,
        )
        self.commit_patcher.start()

    def tearDown(self):  # noqa: D401
        # Stop the patchers and cleanup temp directory
        try:
            self.get_module_path_patcher.stop()
        except Exception:
            pass
        try:
            self.clone_patcher.stop()
        except Exception:
            pass
        try:
            self.commit_patcher.stop()
        except Exception:
            pass
        # restore shutil.rmtree
        try:
            if hasattr(self, "_orig_rmtree"):
                shutil.rmtree = self._orig_rmtree
        except Exception:
            pass
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
        super().tearDown()

    # Helper for get_module_path patch
    def _patched_get_module_path(self, name):
        if name == self.module_name:
            return self.module_path
        # Fallback to the real resolver for other modules
        from odoo.modules.module import get_module_path as real_get_module_path

        return real_get_module_path(name)

    @unittest.skipIf(git is None, "GitPython not installed; skip Git-related tests")
    def test_export_generates_csv_and_commits_on_target_branch(self):
        # Execute export
        action = self.cfg.action_export_csv()
        self.assertIsInstance(action, dict)
        # Expected CSV path under our temp module
        expected_filename = f"{self.cfg.model_id.model}.csv"
        expected_rel = os.path.join("data", expected_filename)
        expected_abs = os.path.join(self.module_path, expected_rel)

        # Assert file exists and has the proper header with External ID first
        self.assertTrue(os.path.exists(expected_abs), f"CSV not found at {expected_abs}")
        with open(expected_abs, encoding="utf-8") as f:
            content = f.read()
        # Simple CSV header check
        header_line = content.splitlines()[0]
        self.assertTrue(header_line.startswith("id,"), f"CSV header must start with 'id,', got: {header_line}")

        # Manifest updated to include the data file
        with open(os.path.join(self.module_path, "__manifest__.py"), encoding="utf-8") as f:
            manifest_txt = f.read()
        self.assertIn(expected_rel, manifest_txt)

        # Git repo should now be on the target branch (repo is initialized at temp root)
        repo = git.Repo(self.temp_dir)
        self.assertEqual(repo.active_branch.name, self.target_branch)

        # And last commit should include our CSV (at least the working tree is clean and file tracked)
        self.assertFalse(repo.is_dirty(untracked_files=True), "Repo should not be dirty after commit")

        # An attachment should be present on the config (CSV stored in chatter)
        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self.cfg._name),
                ("res_id", "=", self.cfg.id),
                ("name", "=", expected_filename),
            ]
        )
        self.assertTrue(attachments, "CSV should be attached in chatter as ir.attachment")
