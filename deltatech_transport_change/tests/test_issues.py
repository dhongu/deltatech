# © 2025 Deltatech / Terrabit
# Regression tests for reported issues

import csv
import io
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

try:
    import git
except Exception:  # pragma: no cover
    git = None

REPO_PATH = "odoo.addons.deltatech_transport_change.models.transport_repo.TransportRepo"


@tagged("post_install", "-at_install")
class TestRelationalCsvHeaders(TransactionCase):
    """#3489: relational values are exported as XML IDs, so the header must use `field/id`."""

    def setUp(self):
        super().setUp()
        model = self.env["ir.model"]._get("res.partner")
        fields = self.env["ir.model.fields"].search(
            [("model_id", "=", model.id), ("name", "in", ("name", "country_id", "category_id"))]
        )
        self.category = self.env["res.partner.category"].create({"name": "Transport Tag Without XMLID"})
        self.partner = self.env["res.partner"].create(
            {
                "name": "Transport Partner",
                "country_id": self.env.ref("base.ro").id,
                "category_id": [(6, 0, self.category.ids)],
            }
        )
        self.cfg = self.env["transport.config"].create(
            {
                "name": "Partners",
                "model_id": model.id,
                "field_ids": [(6, 0, fields.ids)],
                "domain": f"[('id', '=', {self.partner.id})]",
            }
        )

    def _rows(self):
        csv_data, _filename = self.cfg._generate_csv_data()
        rows = list(csv.reader(io.StringIO(csv_data)))
        return rows[0], rows[1:]

    def test_relational_headers_use_id_subfield(self):
        header, rows = self._rows()
        self.assertIn("country_id/id", header)
        self.assertIn("category_id/id", header)
        self.assertIn("name", header)
        row = dict(zip(header, rows[0], strict=True))
        self.assertEqual(row["country_id/id"], "base.ro")
        # a related record without an external ID gets a stable one, not "model,id"
        self.assertEqual(self.env.ref(row["category_id/id"]), self.category)
        self.assertEqual(self.env.ref(row["id"]), self.partner)

    def test_csv_round_trip_resolves_relations_by_xmlid(self):
        # a record whose display name equals the XML ID must not be picked by the importer
        self.env["res.country"].create({"name": "base.ro", "code": "Q9"})
        header, rows = self._rows()
        result = self.env["res.partner"].load(header, rows)
        self.assertFalse([m for m in result["messages"] if m["type"] == "error"], result["messages"])
        self.assertEqual(result["ids"], [self.partner.id])
        self.assertEqual(self.partner.country_id, self.env.ref("base.ro"))
        self.assertEqual(self.partner.category_id, self.category)


@tagged("post_install", "-at_install")
@unittest.skipIf(git is None, "GitPython not installed; skip Git-related tests")
class TestRejectedPush(TransactionCase):
    """#3490: a rejected push must not be reported as a successful export."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="odoo_transport_push_test_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.branch = "main"
        self.bare_dir = os.path.join(self.tmp, "remote.git")
        self.addCleanup(git.Repo.init(self.bare_dir, bare=True).close)

        # seed the remote branch from a first working copy
        self.other = git.Repo.init(os.path.join(self.tmp, "other"))
        self.addCleanup(self.other.close)
        self._config(self.other)
        self.other.git.checkout("-b", self.branch)
        self._commit_file(self.other, "README", "init\n")
        self.other.create_remote("origin", self.bare_dir)
        self.other.git.push("--set-upstream", "origin", self.branch)

        self.repo_rec = self.env["transport.repo"].create(
            {
                "name": "Local Repo",
                "module_name": "my_module",
                "repo_url": self.bare_dir,
                "repo_branch": self.branch,
                "credential_type": "https",
                "username": "user",
                "password": "token",
            }
        )
        patcher = patch(f"{REPO_PATH}._credentialized_url", autospec=True, side_effect=lambda self_, url: url)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _config(self, repo):
        self.addCleanup(repo.close)
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "Test")
            cw.set_value("user", "email", "test@example.com")

    def _commit_file(self, repo, name, content):
        with open(os.path.join(repo.working_tree_dir, name), "w", encoding="utf-8") as f:
            f.write(content)
        repo.git.add(A=True)
        repo.index.commit(f"update {name}")

    def _stale_clone(self):
        """Clone with a tracking branch, then advance the remote so the next push is rejected."""
        clone = git.Repo.clone_from(self.bare_dir, os.path.join(self.tmp, "clone"), branch=self.branch)
        self._config(clone)
        self._commit_file(self.other, "README", "remote advanced\n")
        self.other.git.push("origin", self.branch)
        with open(os.path.join(clone.working_tree_dir, "export.csv"), "w", encoding="utf-8") as f:
            f.write("id,name\n")
        return clone

    def test_rejected_tracked_push_raises(self):
        clone = self._stale_clone()
        self.assertIsNotNone(clone.head.reference.tracking_branch())
        with self.assertRaises(UserError):
            self.repo_rec._commit_and_push(clone, "Transport export")
        remote_files = git.Repo(self.bare_dir).git.ls_tree("-r", "--name-only", self.branch).split()
        self.assertNotIn("export.csv", remote_files)

    def test_successful_tracked_push(self):
        clone = git.Repo.clone_from(self.bare_dir, os.path.join(self.tmp, "clone_ok"), branch=self.branch)
        self._config(clone)
        with open(os.path.join(clone.working_tree_dir, "export.csv"), "w", encoding="utf-8") as f:
            f.write("id,name\n")
        self.repo_rec._commit_and_push(clone, "Transport export")
        remote_files = git.Repo(self.bare_dir).git.ls_tree("-r", "--name-only", self.branch).split()
        self.assertIn("export.csv", remote_files)

    def _config_for_export(self):
        model = self.env["ir.model"]._get("res.partner.category")
        name_field = self.env["ir.model.fields"]._get("res.partner.category", "name")
        self.env["res.partner.category"].create({"name": "Push Test Cat"})
        return self.env["transport.config"].create(
            {
                "name": "Push Test",
                "model_id": model.id,
                "field_ids": [(6, 0, name_field.ids)],
                "domain": "[]",
                "repo_id": self.repo_rec.id,
            }
        )

    def test_failed_push_keeps_last_export_and_warns(self):
        cfg = self._config_for_export()
        module_dir = os.path.join(self.tmp, "export_clone", "my_module")
        os.makedirs(module_dir)
        with open(os.path.join(module_dir, "__manifest__.py"), "w", encoding="utf-8") as f:
            f.write('{"name": "M", "version": "19.0.0.0.1", "data": []}\n')
        clone_repo = git.Repo.init(os.path.join(self.tmp, "export_clone"))
        self.addCleanup(clone_repo.close)
        with (
            patch(
                f"{REPO_PATH}._clone_to_temp",
                autospec=True,
                return_value=(clone_repo.working_tree_dir, clone_repo),
            ),
            patch(f"{REPO_PATH}._commit_and_push", autospec=True, side_effect=UserError("rejected")),
        ):
            action = cfg.action_export_csv()
        self.assertFalse(cfg.last_export)
        self.assertNotEqual(action["params"]["type"], "success")

    def test_failed_clone_keeps_last_export_and_warns(self):
        cfg = self._config_for_export()
        with patch(f"{REPO_PATH}._clone_to_temp", autospec=True, side_effect=UserError("clone failed")):
            action = cfg.action_export_csv()
        self.assertFalse(cfg.last_export)
        self.assertNotEqual(action["params"]["type"], "success")
