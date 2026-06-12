# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Sincronizare git end-to-end pentru librăria de procese, fără rețea.

Folosește un repo git real creat pe disc (clonat prin ``file://``), deci acoperă
fluxul complet: ``sync_git_repos`` → ``_iter_process_sources`` →
``available_processes`` → ``import_processes`` (cu atașarea fișelor).
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from odoo.tests.common import TransactionCase

PARAM_REPOS = "deltatech_business_process.process_library_git_repos"
PARAM_AUTODISCOVER = "deltatech_business_process.process_library_autodiscover"

PROCESS_JSON = {
    "code": "GIT-E2E-001",
    "name": "Proces din git",
    "area": "Git Area",
    "description": "Proces de test sincronizat din git.",
    "steps": [{"name": "Pas unu", "sequence": 10}],
    "tests": [
        {
            "name": "UAT git",
            "scope": "user_acceptance",
            "test_steps": [
                {"step": "Pas unu", "result": "draft"},
                {"step": "Pas inexistent", "result": "draft"},
            ],
        }
    ],
}


class TestLibraryGitSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not shutil.which("git"):
            raise unittest.SkipTest("git is not installed")
        # repo git sursă, pe disc
        cls.tmp = tempfile.mkdtemp()
        cls.repo_dir = os.path.join(cls.tmp, "procese-fixture")
        folder = os.path.join(cls.repo_dir, "GIT001_proces")
        os.makedirs(folder)
        with open(os.path.join(folder, "process.json"), "w", encoding="utf-8") as fh:
            json.dump(PROCESS_JSON, fh)
        with open(os.path.join(folder, "fisa.html"), "w", encoding="utf-8") as fh:
            fh.write("<html><body><h1>Fisa proces git</h1></body></html>")
        shots = os.path.join(folder, "screenshots")
        os.makedirs(shots)
        with open(os.path.join(shots, "01.png"), "wb") as fh:
            fh.write(b"\x89PNG fake")
        # un folder invalid, ca să acopere și citirea cu erori
        bad = os.path.join(cls.repo_dir, "BAD001_invalid")
        os.makedirs(bad)
        with open(os.path.join(bad, "process.json"), "w", encoding="utf-8") as fh:
            fh.write("{not valid json")
        env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
        for cmd in (
            ["git", "init", "--quiet", "."],
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."],
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "--quiet", "-m", "init"],
        ):
            subprocess.run(cmd, cwd=cls.repo_dir, check=True, env=env, capture_output=True)
        cls.repo_url = "file://" + cls.repo_dir

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.library = self.env["business.process.library"]
        self.project = self.env["business.project"].create({"name": "Proiect git e2e"})
        self.icp = self.env["ir.config_parameter"].sudo()
        # cache de clonare izolat, ca să nu atingem data_dir-ul real
        self.cache_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.cache_dir, True)
        patcher = patch.object(type(self.library), "_git_repos_cache_dir", lambda lib, cache=self.cache_dir: cache)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _configure_repo(self):
        self.icp.set_param(PARAM_REPOS, self.repo_url)
        self.icp.set_param(PARAM_AUTODISCOVER, "0")

    def test_sync_clone_then_pull(self):
        self._configure_repo()
        synced = self.library.sync_git_repos()
        self.assertEqual(len(synced), 1)
        label, local_path = synced[0]
        self.assertEqual(label, "procese-fixture")
        self.assertTrue(os.path.isdir(os.path.join(local_path, ".git")))
        # al doilea apel intră pe ramura de pull
        synced2 = self.library.sync_git_repos()
        self.assertEqual(synced2, synced)

    def test_sync_no_repos_configured(self):
        self.icp.set_param(PARAM_REPOS, "")
        self.assertEqual(self.library.sync_git_repos(), [])

    def test_iter_sources_includes_git_repo(self):
        self._configure_repo()
        sources = dict(self.library._iter_process_sources())
        self.assertIn("procese-fixture", sources)

    def test_iter_sources_whitelist(self):
        # whitelist cu un modul fără processes/ și unul inexistent -> doar repo-ul git rămâne
        self._configure_repo()
        self.icp.set_param("deltatech_business_process.process_library_whitelist", "base,no_such_module")
        sources = self.library._iter_process_sources()
        self.assertEqual([label for label, _path in sources], ["procese-fixture"])

    def test_available_and_import_end_to_end(self):
        self._configure_repo()
        available = self.library.available_processes()
        codes = {p["code"]: p for p in available}
        self.assertIn("GIT-E2E-001", codes)
        entry = codes["GIT-E2E-001"]
        self.assertEqual(entry["source_module"], "procese-fixture")
        self.assertTrue(entry["has_screenshots"])

        # importul atașează fișa; forțăm fallback-ul HTML (fără wkhtmltopdf)
        refs = [
            {"module": entry["source_module"], "folder": entry["folder"]},
            {"module": "no_such_source", "folder": "x"},  # ignorat
            None,  # ignorat
        ]
        with patch(
            "odoo.addons.deltatech_business_process.tools.html_to_pdf.html_to_pdf",
            return_value=None,
        ):
            created = self.library.import_processes(refs, project=self.project)
        self.assertEqual(len(created), 1)
        proc = created[0]
        self.assertEqual(proc.code, "GIT-E2E-001")
        self.assertEqual(proc.area_id.name, "Git Area")
        self.assertEqual(len(proc.step_ids), 1)
        # testul importat are doar pasul existent (cel inexistent e sărit)
        test = self.env["business.process.test"].search([("process_id", "=", proc.id)])
        self.assertEqual(len(test), 1)
        self.assertEqual(len(test.test_step_ids), 1)
        # fișa a fost atașată ca HTML (fallback)
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "business.process"), ("res_id", "=", proc.id)]
        )
        self.assertEqual(len(attachment), 1)
        self.assertTrue(attachment.name.endswith(".html"))

        # re-importul aceluiași proces în același proiect e sărit (idempotent)
        with patch(
            "odoo.addons.deltatech_business_process.tools.html_to_pdf.html_to_pdf",
            return_value=None,
        ):
            again = self.library.import_processes(refs, project=self.project)
        self.assertFalse(again)

    def test_import_attaches_pdf_when_conversion_works(self):
        self._configure_repo()
        available = self.library.available_processes()
        entry = next(p for p in available if p["code"] == "GIT-E2E-001")
        with patch(
            "odoo.addons.deltatech_business_process.tools.html_to_pdf.html_to_pdf",
            return_value=b"%PDF-1.4 fake",
        ):
            created = self.library.import_processes(
                [{"module": entry["source_module"], "folder": entry["folder"]}], project=self.project
            )
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "business.process"), ("res_id", "=", created.id)]
        )
        self.assertEqual(attachment.mimetype, "application/pdf")

    def test_settings_action_sync(self):
        settings = self.env["res.config.settings"].create({})
        self._configure_repo()
        action = settings.action_sync_git_repos()
        self.assertEqual(action["tag"], "display_notification")
        self.assertIn("procese-fixture", action["params"]["message"])

        self.icp.set_param(PARAM_REPOS, "")
        action = settings.action_sync_git_repos()
        self.assertIn("No git repositories", action["params"]["message"])


class TestLibraryHelpers(TransactionCase):
    """Ramuri mărunte din engine, fără repo git."""

    def setUp(self):
        super().setUp()
        self.library = self.env["business.process.library"]
        self.project = self.env["business.project"].create({"name": "Proiect helperi"})

    def _make_process(self, name, area):
        return self.env["business.process"].create({"name": name, "area_id": area.id, "project_id": self.project.id})

    def test_module_processes_dir_missing(self):
        self.assertIsNone(self.library._module_processes_dir("no_such_module"))
        # modul real, dar fără folder processes/
        self.assertIsNone(self.library._module_processes_dir("base"))

    def test_read_folder_missing_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.library._read_folder(tmp, "missing"), [])
            os.makedirs(os.path.join(tmp, "bad"))
            with open(os.path.join(tmp, "bad", "process.json"), "w", encoding="utf-8") as fh:
                fh.write("{broken")
            self.assertEqual(self.library._read_folder(tmp, "bad"), [])
            # un JSON listă e întors ca atare
            os.makedirs(os.path.join(tmp, "list"))
            with open(os.path.join(tmp, "list", "process.json"), "w", encoding="utf-8") as fh:
                json.dump([{"code": "A"}, {"code": "B"}], fh)
            self.assertEqual(len(self.library._read_folder(tmp, "list")), 2)

    def test_get_or_create_area(self):
        self.assertFalse(self.library._get_or_create_area(""))
        area = self.library._get_or_create_area("Arie nouă din test")
        self.assertTrue(area)
        self.assertEqual(self.library._get_or_create_area("Arie nouă din test"), area)

    def test_attach_bytes_idempotent(self):
        area = self.library._get_or_create_area("Atasamente")
        process = self._make_process("P atasamente", area)
        # conținut gol -> nimic atașat
        self.library._attach_bytes(process, "x.txt", b"", "text/plain")
        domain = [("res_model", "=", "business.process"), ("res_id", "=", process.id)]
        self.assertFalse(self.env["ir.attachment"].search(domain))
        # de două ori același nume -> un singur atașament, actualizat
        self.library._attach_bytes(process, "x.txt", b"v1", "text/plain")
        self.library._attach_bytes(process, "x.txt", b"v2", "text/plain")
        attachments = self.env["ir.attachment"].search(domain)
        self.assertEqual(len(attachments), 1)

    def test_attach_fisa_empty_html(self):
        area = self.library._get_or_create_area("Fisa goala")
        process = self._make_process("P fisa", area)
        self.library._attach_fisa(process, "Sheet", "")
        domain = [("res_model", "=", "business.process"), ("res_id", "=", process.id)]
        self.assertFalse(self.env["ir.attachment"].search(domain))

    def test_sync_git_repo_timeout_and_error(self):
        with tempfile.TemporaryDirectory() as cache:
            with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=1)):
                self.assertIsNone(self.library._sync_git_repo("https://example.com/r.git", cache))
            with patch.object(subprocess, "run", side_effect=RuntimeError("boom")):
                self.assertIsNone(self.library._sync_git_repo("https://example.com/r.git", cache))

    def test_sync_git_repo_pull_failure_keeps_local(self):
        # un pull eșuat păstrează clona locală existentă
        with tempfile.TemporaryDirectory() as cache:
            local = os.path.join(cache, "r")
            os.makedirs(os.path.join(local, ".git"))

            def fake_run(cmd, **kwargs):
                class R:
                    returncode = 1
                    stderr = "network down"

                return R()

            with patch.object(subprocess, "run", side_effect=fake_run):
                self.assertEqual(self.library._sync_git_repo("https://example.com/r.git", cache), local)
