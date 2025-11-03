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
        # Create a temporary fake module folder that will act as `deltatech_test`
        self.temp_dir = tempfile.mkdtemp(prefix="odoo_transport_test_")
        self.module_name = "deltatech_test"
        self.module_path = os.path.join(self.temp_dir, self.module_name)
        os.makedirs(self.module_path, exist_ok=True)
        os.makedirs(os.path.join(self.module_path, "data"), exist_ok=True)
        # Minimal manifest
        manifest_content = "{'name': 'deltatech_test',\n'version': '1.0.0.0.0',\n'depends': ['base'],\n'data': [],\n}\n"
        with open(os.path.join(self.module_path, "__manifest__.py"), "w", encoding="utf-8") as f:
            f.write(manifest_content)

        # Initialize a local git repository in the temp module
        self.repo = git.Repo.init(self.module_path)
        # Configure identity (required by git for commits)
        with self.repo.config_writer() as cw:
            cw.set_value("user", "name", "Odoo Test")
            cw.set_value("user", "email", "odoo@test.local")
        # Stage and initial commit
        self.repo.index.add(["__manifest__.py"])
        self.repo.index.commit("Initial commit for test module")

        # Create and checkout to a different branch than the target to ensure switch happens
        other_branch = self.repo.create_head("other_branch")
        other_branch.checkout()

        # Target branch we want the exporter to use
        self.target_branch = "test_branch"

        # Patch get_module_path so that our module name resolves to the temp path
        self.get_module_path_patcher = patch(
            "odoo.modules.module.get_module_path",
            side_effect=self._patched_get_module_path,
        )
        self.get_module_path_patcher.start()

        # Create a repo configuration record
        self.repo_rec = self.env["transport.repo"].create(
            {
                "name": "Test Repo",
                "module_name": self.module_name,
                # No remote URL -> commit local only
                "repo_url": "",
                "repo_branch": self.target_branch,
                "credential_type": "ssh",
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

    def tearDown(self):  # noqa: D401
        # Stop the patcher and cleanup temp directory
        try:
            self.get_module_path_patcher.stop()
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

        # Git repo should now be on the target branch
        repo = git.Repo(self.module_path)
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
