# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Sincronizare git end-to-end pentru librăria de procese, fără rețea.

Folosește un repo git real creat pe disc (clonat prin ``file://``), deci acoperă
fluxul complet: ``sync_git_repos`` → ``_iter_process_sources`` →
``available_processes`` → ``import_processes`` (cu atașarea fișelor).
"""

import base64
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
PARAM_TOKEN = "deltatech_business_process.process_library_git_token"
PARAM_USER = "deltatech_business_process.process_library_git_user"

PROCESS_JSON = {
    "code": "GIT-E2E-001",
    "name": "Proces din git",
    "area": "Git Area",
    "process_group": "Grup git",
    "module_type": "standard",
    "implementation_stage": "first_stage",
    "state": "design",
    "description": "Proces de test sincronizat din git.",
    "include_durations": True,
    "configuration_duration": 0.5,
    "instructing_duration": 0.25,
    "data_migration_duration": 0.0,
    "testing_duration": 1.0,
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
        # Certain hardened environments (e.g. CI build sandboxes) set
        # ``protocol.file.allow=never`` system-wide, which would break the
        # ``file://`` transport this fixture relies on to simulate a real repo
        # without network access. Force it back on for the git calls made by
        # the code under test — this only affects the test's own subprocess
        # invocations, never production traffic (which is https/ssh).
        original_auth_args = type(self.library)._git_auth_args

        def _patched_auth_args(lib, url, _orig=original_auth_args):
            args = _orig(lib, url)
            if url.startswith("file://"):
                args = ["-c", "protocol.file.allow=always", *args]
            return args

        auth_patcher = patch.object(type(self.library), "_git_auth_args", _patched_auth_args)
        auth_patcher.start()
        self.addCleanup(auth_patcher.stop)

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
        # metadatele și duratele se importă implicit (include_durations=True)
        self.assertEqual(proc.process_group_id.name, "Grup git")
        self.assertEqual(proc.module_type, "standard")
        self.assertEqual(proc.implementation_stage_id.name, "First stage")
        self.assertEqual(proc.state, "design")
        self.assertAlmostEqual(proc.configuration_duration, 0.5)
        self.assertAlmostEqual(proc.duration_for_completion, 0.5 + 0.25 + 0.0 + 1.0)
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

    def test_options_dialog_all_or_nothing_durations(self):
        # Dialogul de opțiuni propagă alegerea (all-or-nothing) prin context,
        # iar importul din listă o respectă pentru toate procesele selectate.
        self._configure_repo()
        ctx = {"active_model": "business.project", "active_ids": self.project.ids}
        options = (
            self.env["business.process.library.import.options"].with_context(**ctx).create({"include_durations": False})
        )
        action = options.action_show_library()
        self.assertFalse(action["context"]["library_include_durations"])

        # importăm liniile prin butonul listei, sub același context
        line_model = self.env["business.process.library.import.line"].with_context(**action["context"])
        lines = line_model.search([("project_id", "=", self.project.id), ("code", "=", "GIT-E2E-001")])
        self.assertTrue(lines)
        with patch(
            "odoo.addons.deltatech_business_process.tools.html_to_pdf.html_to_pdf",
            return_value=None,
        ):
            lines.action_import_selected()
        proc = self.env["business.process"].search([("code", "=", "GIT-E2E-001"), ("project_id", "=", self.project.id)])
        self.assertEqual(len(proc), 1)
        # duratele sărite, dar restul metadatelor importate
        self.assertEqual(proc.configuration_duration, 0.0)
        self.assertEqual(proc.testing_duration, 0.0)
        self.assertEqual(proc.module_type, "standard")

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

    def _meta_process_data(self):
        return {
            "code": "META-001",
            "name": "Proces cu metadate",
            "area": "Achizitie",
            "process_group": "Produse stocabile",
            "module_type": "standard",
            "implementation_stage": "first_stage",  # cheie legacy -> "First stage"
            "state": "design",
            "include_durations": True,
            "configuration_duration": 0.1667,
            "instructing_duration": 0.4167,
            "data_migration_duration": 0.0,
            "testing_duration": 0.625,
            "steps": [],
        }

    def test_load_process_imports_durations_and_meta(self):
        proc = self.library._load_process(self._meta_process_data(), project=self.project)
        self.assertEqual(proc.process_group_id.name, "Produse stocabile")
        self.assertEqual(proc.module_type, "standard")
        self.assertEqual(proc.implementation_stage_id.name, "First stage")
        self.assertEqual(proc.state, "design")
        self.assertAlmostEqual(proc.configuration_duration, 0.1667)
        self.assertAlmostEqual(proc.testing_duration, 0.625)
        # totalul e calculat din cele patru componente
        self.assertAlmostEqual(proc.duration_for_completion, 0.1667 + 0.4167 + 0.0 + 0.625)

    def test_load_process_can_skip_durations(self):
        data = dict(self._meta_process_data(), code="META-002")
        proc = self.library._load_process(data, project=self.project, include_durations=False)
        # metadatele rămân, dar duratele nu se importă
        self.assertEqual(proc.module_type, "standard")
        self.assertEqual(proc.configuration_duration, 0.0)
        self.assertEqual(proc.testing_duration, 0.0)
        self.assertEqual(proc.duration_for_completion, 0.0)

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

    def test_safe_url_strips_credentials(self):
        self.assertEqual(
            self.library._safe_url("https://user:tok@github.com/org/repo.git"),
            "https://github.com/org/repo.git",
        )
        # fără credențiale / non-http rămâne neschimbat
        self.assertEqual(self.library._safe_url("https://github.com/org/repo.git"), "https://github.com/org/repo.git")
        self.assertEqual(self.library._safe_url("git@github.com:org/repo.git"), "git@github.com:org/repo.git")

    def test_git_env_is_non_interactive(self):
        env = self.library._git_env()
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertIn("BatchMode=yes", env["GIT_SSH_COMMAND"])

    def test_git_auth_args(self):
        icp = self.env["ir.config_parameter"].sudo()
        # fără token -> fără args, indiferent de URL
        icp.set_param(PARAM_TOKEN, "")
        self.assertEqual(self.library._git_auth_args("https://github.com/org/repo.git"), [])
        # cu token -> header Basic cu userul implicit x-access-token
        icp.set_param(PARAM_TOKEN, "ghp_secret")
        icp.set_param(PARAM_USER, "")
        args = self.library._git_auth_args("https://github.com/org/repo.git")
        expected = base64.b64encode(b"x-access-token:ghp_secret").decode()
        self.assertEqual(args, ["-c", f"http.extraHeader=Authorization: Basic {expected}"])
        # user explicit (GitLab)
        icp.set_param(PARAM_USER, "oauth2")
        args = self.library._git_auth_args("https://gitlab.com/org/repo.git")
        expected = base64.b64encode(b"oauth2:ghp_secret").decode()
        self.assertEqual(args[1], f"http.extraHeader=Authorization: Basic {expected}")
        # ssh / url cu credențiale deja incluse / non-https -> fără injectare
        self.assertEqual(self.library._git_auth_args("git@github.com:org/repo.git"), [])
        self.assertEqual(self.library._git_auth_args("https://u:p@github.com/org/repo.git"), [])
        self.assertEqual(self.library._git_auth_args("file:///tmp/repo"), [])

    def test_clone_passes_auth_header_and_env(self):
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param(PARAM_TOKEN, "ghp_secret")
        icp.set_param(PARAM_USER, "x-access-token")
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["env"] = kwargs.get("env")

            class R:
                returncode = 1  # forțăm eșec ca să nu atingem discul mai departe
                stderr = "auth ok, dar oprim aici"

            return R()

        with tempfile.TemporaryDirectory() as cache:
            with patch.object(subprocess, "run", side_effect=fake_run):
                self.library._sync_git_repo("https://github.com/org/privat.git", cache)
        expected = base64.b64encode(b"x-access-token:ghp_secret").decode()
        self.assertIn("-c", captured["cmd"])
        self.assertIn(f"http.extraHeader=Authorization: Basic {expected}", captured["cmd"])
        # antetul vine ÎNAINTE de subcomanda clone
        self.assertLess(captured["cmd"].index("-c"), captured["cmd"].index("clone"))
        self.assertEqual(captured["env"]["GIT_TERMINAL_PROMPT"], "0")

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
