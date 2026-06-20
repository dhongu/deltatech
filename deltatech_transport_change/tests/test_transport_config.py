# © 2025 Deltatech / Terrabit
# Tests for TransportConfig model

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

try:
    import git
except Exception:  # pragma: no cover
    git = None


class TestTransportConfigValidation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.model = self.env["ir.model"].search([("model", "=", "res.partner.category")], limit=1)
        self.name_field = self.env["ir.model.fields"].search(
            [("model_id", "=", self.model.id), ("name", "=", "name")], limit=1
        )
        self.other_model = self.env["ir.model"].search([("model", "=", "res.partner")], limit=1)
        self.other_field = self.env["ir.model.fields"].search(
            [("model_id", "=", self.other_model.id), ("name", "=", "name")], limit=1
        )

    def test_create_config_without_repo_succeeds(self):
        cfg = self.env["transport.config"].create(
            {
                "name": "No Repo Config",
                "model_id": self.model.id,
                "field_ids": [(6, 0, [self.name_field.id])],
                "domain": "[]",
            }
        )
        self.assertTrue(cfg.id)

    def test_field_from_wrong_model_raises(self):
        with self.assertRaises(ValidationError):
            self.env["transport.config"].create(
                {
                    "name": "Bad Fields Config",
                    "model_id": self.model.id,
                    "field_ids": [(6, 0, [self.other_field.id])],
                    "domain": "[]",
                }
            )

    def test_onchange_model_clears_fields(self):
        cfg = self.env["transport.config"].new(
            {
                "name": "Onchange Test",
                "model_id": self.model.id,
                "field_ids": [(6, 0, [self.name_field.id])],
            }
        )
        # simulate model change
        cfg.model_id = self.other_model
        cfg._onchange_model_id()
        self.assertFalse(cfg.field_ids)

    def test_onchange_model_sets_name(self):
        cfg = self.env["transport.config"].new({"name": "Old Name"})
        cfg.model_id = self.model
        cfg._onchange_model_id()
        self.assertEqual(cfg.name, self.model.name)


class TestTransportConfigGenerateCsv(TransactionCase):
    def setUp(self):
        super().setUp()
        self.model = self.env["ir.model"].search([("model", "=", "res.partner.category")], limit=1)
        self.name_field = self.env["ir.model.fields"].search(
            [("model_id", "=", self.model.id), ("name", "=", "name")], limit=1
        )
        self.cat = self.env["res.partner.category"].create({"name": "Export Cat"})

    def _make_config(self, domain="[]", fields=None):
        if fields is None:
            fields = [self.name_field.id]
        return self.env["transport.config"].create(
            {
                "name": "CSV Test Config",
                "model_id": self.model.id,
                "field_ids": [(6, 0, fields)],
                "domain": domain,
            }
        )

    def test_generate_csv_has_id_column(self):
        cfg = self._make_config()
        csv_data, filename = cfg._generate_csv_data()
        header = csv_data.splitlines()[0]
        self.assertTrue(header.startswith("id,"), f"Header should start with 'id,', got: {header}")

    def test_generate_csv_filename_matches_model(self):
        cfg = self._make_config()
        _, filename = cfg._generate_csv_data()
        self.assertEqual(filename, "res.partner.category.csv")

    def test_generate_csv_contains_record(self):
        cfg = self._make_config()
        csv_data, _ = cfg._generate_csv_data()
        self.assertIn("Export Cat", csv_data)

    def test_generate_csv_domain_filters_records(self):
        # Domain that matches nothing
        cfg = self._make_config(domain="[('name', '=', '__no_such_category__')]")
        with self.assertRaises(UserError):
            cfg._generate_csv_data()

    def test_generate_csv_no_fields_raises(self):
        cfg = self.env["transport.config"].create(
            {
                "name": "No Fields",
                "model_id": self.model.id,
                "domain": "[]",
            }
        )
        with self.assertRaises(UserError):
            cfg._generate_csv_data()

    def test_attach_csv_creates_attachment(self):
        cfg = self._make_config()
        csv_data, filename = cfg._generate_csv_data()
        cfg._attach_csv_in_chatter(filename, csv_data)
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", cfg._name), ("res_id", "=", cfg.id), ("name", "=", filename)]
        )
        self.assertTrue(attachment, "Attachment should be created in chatter")


@unittest.skipIf(git is None, "GitPython not installed; skip Git-related tests")
class TestTransportConfigExportNoRepo(TransactionCase):
    def setUp(self):
        super().setUp()
        self.model = self.env["ir.model"].search([("model", "=", "res.partner.category")], limit=1)
        self.name_field = self.env["ir.model.fields"].search(
            [("model_id", "=", self.model.id), ("name", "=", "name")], limit=1
        )
        self.env["res.partner.category"].create({"name": "Export No Repo Cat"})

    def test_export_without_repo_raises(self):
        cfg = self.env["transport.config"].create(
            {
                "name": "No Repo Export",
                "model_id": self.model.id,
                "field_ids": [(6, 0, [self.name_field.id])],
                "domain": "[]",
            }
        )
        with self.assertRaises(UserError):
            cfg.action_export_csv()

    def test_export_repo_without_module_name_raises(self):
        # module_name is required field, so test with an empty-ish repo name
        repo = self.env["transport.repo"].create(
            {
                "name": "No Module Repo",
                "module_name": "some_module",
                "repo_url": "https://example.com/repo.git",
                "repo_branch": "main",
                "credential_type": "https",
                "username": "u",
                "password": "p",
            }
        )
        # Force module_name to empty via SQL to bypass required constraint
        self.env.cr.execute("UPDATE transport_repo SET module_name = '' WHERE id = %s", [repo.id])
        repo.invalidate_recordset()
        cfg = self.env["transport.config"].create(
            {
                "name": "Empty Module Name",
                "model_id": self.model.id,
                "field_ids": [(6, 0, [self.name_field.id])],
                "domain": "[]",
                "repo_id": repo.id,
            }
        )
        with self.assertRaises(UserError):
            cfg.action_export_csv()


@unittest.skipIf(git is None, "GitPython not installed; skip Git-related tests")
class TestTransportConfigMultiExport(TransactionCase):
    """Test exporting multiple configs in a single call."""

    def setUp(self):
        super().setUp()
        self.module_name = "deltatech_multi_test"
        self.target_branch = "test_multi_branch"

        self.repo_rec = self.env["transport.repo"].create(
            {
                "name": "Multi Export Repo",
                "module_name": self.module_name,
                "repo_url": "https://example.com/org/repo.git",
                "repo_branch": self.target_branch,
                "credential_type": "https",
                "username": "user",
                "password": "token",
            }
        )

        # Two models for two configs
        self.cat_model = self.env["ir.model"].search([("model", "=", "res.partner.category")], limit=1)
        self.cat_name_field = self.env["ir.model.fields"].search(
            [("model_id", "=", self.cat_model.id), ("name", "=", "name")], limit=1
        )
        self.env["res.partner.category"].create({"name": "Multi Cat"})

        self.cfg1 = self.env["transport.config"].create(
            {
                "name": "Multi Export 1",
                "model_id": self.cat_model.id,
                "field_ids": [(6, 0, [self.cat_name_field.id])],
                "domain": "[]",
                "repo_id": self.repo_rec.id,
            }
        )
        self.cfg2 = self.env["transport.config"].create(
            {
                "name": "Multi Export 2",
                "model_id": self.cat_model.id,
                "field_ids": [(6, 0, [self.cat_name_field.id])],
                "domain": "[]",
                "repo_id": self.repo_rec.id,
            }
        )

        # Set up temp git repo
        self._orig_rmtree = shutil.rmtree
        self.temp_dir = tempfile.mkdtemp(prefix="odoo_multi_export_test_")

        def _no_rmtree(path, *args, **kwargs):
            if os.path.abspath(path) == os.path.abspath(self.temp_dir):
                return
            return self._orig_rmtree(path, *args, **kwargs)

        shutil.rmtree = _no_rmtree

        module_path = os.path.join(self.temp_dir, self.module_name)
        os.makedirs(os.path.join(module_path, "data"), exist_ok=True)
        with open(os.path.join(module_path, "__manifest__.py"), "w", encoding="utf-8") as f:
            f.write('{"name": "Multi Test", "version": "19.0.0.0.1", "data": []}\n')

        self.repo = git.Repo.init(self.temp_dir)
        self.repo.git.add(A=True)
        self.repo.index.commit("init")
        self.repo.create_head(self.target_branch)
        self.repo.git.checkout(self.target_branch)

        self.clone_patcher = patch(
            "odoo.addons.deltatech_transport_change.models.transport_repo.TransportRepo.clone_to_temp",
            autospec=True,
            return_value=(self.temp_dir, self.repo),
        )
        self.clone_patcher.start()

        def _local_commit(self_repo, repo_obj, commit_message):
            repo_obj.git.add(A=True)
            if repo_obj.is_dirty(index=True, working_tree=True, untracked_files=True):
                repo_obj.index.commit(commit_message)

        self.commit_patcher = patch(
            "odoo.addons.deltatech_transport_change.models.transport_repo.TransportRepo.commit_and_push",
            autospec=True,
            side_effect=_local_commit,
        )
        self.commit_patcher.start()

    def tearDown(self):
        try:
            self.clone_patcher.stop()
        except Exception:
            pass
        try:
            self.commit_patcher.stop()
        except Exception:
            pass
        try:
            shutil.rmtree = self._orig_rmtree
        except Exception:
            pass
        try:
            self._orig_rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
        super().tearDown()

    def test_multi_config_export_both_csvs_created(self):
        configs = self.cfg1 | self.cfg2
        action = configs.action_export_csv()
        self.assertIsInstance(action, dict)

        module_path = os.path.join(self.temp_dir, self.module_name)
        expected_csv = os.path.join(module_path, "data", "res.partner.category.csv")
        self.assertTrue(os.path.exists(expected_csv))

    def test_multi_config_last_export_updated(self):
        self.assertFalse(self.cfg1.last_export)
        self.assertFalse(self.cfg2.last_export)
        configs = self.cfg1 | self.cfg2
        configs.action_export_csv()
        self.assertTrue(self.cfg1.last_export)
        self.assertTrue(self.cfg2.last_export)

    def test_multi_config_manifest_version_bumped_once(self):
        module_path = os.path.join(self.temp_dir, self.module_name)
        manifest_path = os.path.join(module_path, "__manifest__.py")

        configs = self.cfg1 | self.cfg2
        configs.action_export_csv()

        import ast

        with open(manifest_path, encoding="utf-8") as f:
            data = ast.literal_eval(f.read())
        # Version should have been bumped exactly once: 19.0.0.0.1 → 19.0.0.0.2
        self.assertEqual(data.get("version"), "19.0.0.0.2")
