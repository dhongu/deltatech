# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Test de încărcare a proceselor din repo-ul standalone ``procese/``.

Verifică că:
- Toate fișierele ``process.json`` din ``procese/`` pot fi citite (inclusiv UTF-8 BOM).
- ``available_processes()`` returnează procesele așteptate când sursa e repo-ul standalone.
- ``import_processes()`` creează înregistrări ``business.process`` valide pentru un eșantion.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

PROCESE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "procese"))


def _iter_process_sources_from_repo(self):
    """Returnează direct folderul standalone ``procese/`` ca sursă unică."""
    if not os.path.isdir(PROCESE_DIR):
        return []
    return [("procese_repo", PROCESE_DIR)]


class TestProcessLibraryRo(TransactionCase):
    """Validarea proceselor din repo-ul standalone procese/."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._procese_dir_exists = os.path.isdir(PROCESE_DIR)
        if cls._procese_dir_exists:
            cls._process_folders = sorted(
                f for f in os.listdir(PROCESE_DIR) if os.path.isfile(os.path.join(PROCESE_DIR, f, "process.json"))
            )

    def setUp(self):
        super().setUp()
        self.project = self.env["business.project"].create({"name": "Test Repo Procese"})

    def _require_repo(self):
        if not self._procese_dir_exists:
            self.skipTest(f"Repo procese/ nu există la: {PROCESE_DIR}")

    # ------------------------------------------------------------------
    # 1. Validare JSON pură — fără Odoo
    # ------------------------------------------------------------------

    def test_all_jsons_parseable(self):
        """Toate process.json trebuie să se parseze corect (inclusiv BOM)."""
        self._require_repo()
        errors = []
        for folder in self._process_folders:
            path = os.path.join(PROCESE_DIR, folder, "process.json")
            try:
                with open(path, encoding="utf-8-sig") as fh:
                    json.load(fh)
            except Exception as exc:
                errors.append(f"{folder}: {exc}")
        self.assertFalse(errors, "JSON-uri cu erori de parsare:\n" + "\n".join(errors))

    def test_all_jsons_have_required_fields(self):
        """Fiecare process.json trebuie să aibă ``code``, ``name`` și ``area``."""
        self._require_repo()
        missing = []
        for folder in self._process_folders:
            path = os.path.join(PROCESE_DIR, folder, "process.json")
            try:
                with open(path, encoding="utf-8-sig") as fh:
                    data = json.load(fh)
            except Exception:
                continue
            for field in ("code", "name", "area"):
                if not data.get(field):
                    missing.append(f"{folder}: câmp lipsă/gol '{field}'")
        self.assertFalse(missing, "Câmpuri obligatorii lipsă:\n" + "\n".join(missing))

    def test_process_codes_are_unique(self):
        """Codurile din process.json trebuie să fie unice în repo."""
        self._require_repo()
        codes = {}
        for folder in self._process_folders:
            path = os.path.join(PROCESE_DIR, folder, "process.json")
            try:
                with open(path, encoding="utf-8-sig") as fh:
                    data = json.load(fh)
            except Exception:
                continue
            code = data.get("code")
            if code:
                codes.setdefault(code, []).append(folder)
        duplicates = {c: fs for c, fs in codes.items() if len(fs) > 1}
        self.assertFalse(duplicates, "Coduri duplicate în repo:\n" + str(duplicates))

    # ------------------------------------------------------------------
    # 2. available_processes() via engine Odoo
    # ------------------------------------------------------------------

    def test_available_processes_from_repo(self):
        """available_processes() trebuie să descopere procesele din repo standalone."""
        self._require_repo()
        library = self.env["business.process.library"]
        with patch.object(type(library), "_iter_process_sources", _iter_process_sources_from_repo):
            result = library.available_processes()

        self.assertTrue(result, "available_processes() nu a returnat nimic din procese/")
        self.assertEqual(
            len(result),
            len(self._process_folders),
            f"Așteptat {len(self._process_folders)} procese, găsite {len(result)}",
        )
        # fiecare intrare trebuie să aibă câmpurile de bază
        for item in result:
            self.assertIn("code", item)
            self.assertIn("name", item)
            self.assertIn("folder", item)

    # ------------------------------------------------------------------
    # 3. import_processes() — eșantion de 3 procese
    # ------------------------------------------------------------------

    def test_import_sample_processes(self):
        """import_processes() creează înregistrări business.process valide (eșantion 3)."""
        self._require_repo()
        sample_folders = self._process_folders[:3]
        refs = [{"module": "procese_repo", "folder": f} for f in sample_folders]

        library = self.env["business.process.library"]
        with patch.object(type(library), "_iter_process_sources", _iter_process_sources_from_repo):
            created = library.import_processes(refs, project=self.project)

        self.assertEqual(
            len(created),
            len(sample_folders),
            f"Așteptat {len(sample_folders)} procese create, obținut {len(created)}",
        )
        for proc in created:
            self.assertTrue(proc.name, "Procesul creat nu are name")
            self.assertTrue(proc.code, "Procesul creat nu are code")
            self.assertEqual(proc.project_id, self.project)

    def test_import_all_processes(self):
        """import_processes() creează câte un business.process pentru fiecare folder din repo."""
        self._require_repo()
        refs = [{"module": "procese_repo", "folder": f} for f in self._process_folders]

        library = self.env["business.process.library"]
        with patch.object(type(library), "_iter_process_sources", _iter_process_sources_from_repo):
            created = library.import_processes(refs, project=self.project)

        self.assertEqual(
            len(created),
            len(self._process_folders),
            f"Așteptat {len(self._process_folders)} procese, create {len(created)}",
        )

    # ------------------------------------------------------------------
    # 4. Selecție grupată (acțiune list-view reală)
    # ------------------------------------------------------------------

    def test_action_open_library_populates_grouped(self):
        """action_open_library populează liniile cu area_id și cere grupare după arie."""
        self._require_repo()
        Line = self.env["business.process.library.import.line"]
        library = self.env["business.process.library"]
        with patch.object(type(library), "_iter_process_sources", _iter_process_sources_from_repo):
            action = Line.with_context(
                active_model="business.project", active_ids=[self.project.id]
            ).action_open_library()

        # acțiunea cere gruparea după arie
        self.assertEqual(action["context"].get("group_by"), ["area_id"])
        # liniile au fost create pentru proiect, cu area_id setat
        lines = Line.search([("project_id", "=", self.project.id)])
        self.assertEqual(len(lines), len(self._process_folders))
        self.assertTrue(all(line.area_id for line in lines), "Toate liniile trebuie să aibă area_id")

    def test_action_import_selected_imports_into_project(self):
        """action_import_selected importă liniile selectate în proiectul lor."""
        self._require_repo()
        Line = self.env["business.process.library.import.line"]
        library = self.env["business.process.library"]
        with patch.object(type(library), "_iter_process_sources", _iter_process_sources_from_repo):
            Line.with_context(active_model="business.project", active_ids=[self.project.id]).action_open_library()
            lines = Line.search([("project_id", "=", self.project.id)])
            selected = lines[:3]
            selected.action_import_selected()

        created = self.env["business.process"].search([("project_id", "=", self.project.id)])
        self.assertEqual(len(created), 3, "Trebuie importate exact 3 procese selectate")


class TestProcessLibraryGit(TransactionCase):
    """Testează integrarea cu repo-uri git (fără rețea — subprocess mock)."""

    def setUp(self):
        super().setUp()
        self.project = self.env["business.project"].create({"name": "Test Git Procese"})

    def _make_fake_repo(self, tmp_dir, processes):
        """Creează un folder care simulează un repo git cu process.json-uri."""
        os.makedirs(os.path.join(tmp_dir, ".git"))
        for folder, data in processes.items():
            process_dir = os.path.join(tmp_dir, folder)
            os.makedirs(process_dir)
            with open(os.path.join(process_dir, "process.json"), "w", encoding="utf-8") as f:
                json.dump(data, f)
        return tmp_dir

    def test_sync_git_repo_clone(self):
        """_sync_git_repo apelează git clone când repo-ul nu există local."""
        library = self.env["business.process.library"]
        with tempfile.TemporaryDirectory() as tmp_cache:
            fake_url = "https://github.com/terrabit-ro/procese"
            local_path = os.path.join(tmp_cache, "procese")
            os.makedirs(os.path.join(local_path, ".git"))  # simulează clone reușit

            def fake_run(cmd, **kwargs):
                result = MagicMock()
                result.returncode = 0
                result.stderr = ""
                os.makedirs(os.path.join(tmp_cache, "procese", ".git"), exist_ok=True)
                return result

            with patch("subprocess.run", side_effect=fake_run):
                result = library._sync_git_repo(fake_url, tmp_cache)

            self.assertEqual(result, local_path)

    def test_sync_git_repo_pull(self):
        """_sync_git_repo apelează git pull când repo-ul există deja."""
        library = self.env["business.process.library"]
        with tempfile.TemporaryDirectory() as tmp_cache:
            fake_url = "https://github.com/terrabit-ro/procese"
            local_path = os.path.join(tmp_cache, "procese")
            os.makedirs(os.path.join(local_path, ".git"))  # simulează repo existent

            calls = []

            def fake_run(cmd, **kwargs):
                calls.append(cmd)
                result = MagicMock()
                result.returncode = 0
                result.stderr = ""
                return result

            with patch("subprocess.run", side_effect=fake_run):
                result = library._sync_git_repo(fake_url, tmp_cache)

            self.assertEqual(result, local_path)
            # trebuie să fi apelat git pull (nu clone)
            self.assertTrue(any("pull" in cmd for cmd in calls), "Așteptat git pull, nu clone")
            self.assertFalse(any("clone" in cmd for cmd in calls), "Nu trebuia git clone pe repo existent")

    def test_sync_git_repo_failure_returns_none(self):
        """_sync_git_repo returnează None când git clone eșuează."""
        library = self.env["business.process.library"]
        with tempfile.TemporaryDirectory() as tmp_cache:

            def fake_run_fail(cmd, **kwargs):
                result = MagicMock()
                result.returncode = 128
                result.stderr = "fatal: repository not found"
                return result

            with patch("subprocess.run", side_effect=fake_run_fail):
                result = library._sync_git_repo("https://github.com/inexistent/repo", tmp_cache)

            self.assertIsNone(result)

    def test_available_processes_from_git_repo(self):
        """available_processes() returnează procesele dintr-un repo git configurat."""
        library = self.env["business.process.library"]
        with tempfile.TemporaryDirectory() as tmp_repo:
            self._make_fake_repo(
                tmp_repo,
                {
                    "AC001_test": {"code": "AC001", "name": "Test Achiziție", "area": "Achizitie"},
                    "CB001_test": {"code": "CB001", "name": "Test Contabilitate", "area": "Contabilitate"},
                },
            )

            def fake_sync_git_repos(self_lib):
                return [("procese", tmp_repo)]

            with patch.object(type(library), "sync_git_repos", fake_sync_git_repos):
                # dezactivăm autodiscover ca să nu adauge zgomot din modulele instalate
                with patch.object(type(library), "_iter_process_sources", lambda s: [("procese", tmp_repo)]):
                    result = library.available_processes()

        codes = [r["code"] for r in result]
        self.assertIn("AC001", codes)
        self.assertIn("CB001", codes)

    def test_import_processes_from_git_repo(self):
        """import_processes() creează business.process din procese descărcate via git."""
        library = self.env["business.process.library"]
        with tempfile.TemporaryDirectory() as tmp_repo:
            self._make_fake_repo(
                tmp_repo,
                {
                    "AC001_test": {
                        "code": "GITAC001",
                        "name": "Achiziție Git",
                        "area": "Achizitie",
                        "steps": [{"code": "01", "name": "Pas 1", "sequence": 10}],
                        "tests": [
                            {"name": "UAT GITAC001", "scope": "user_acceptance", "state": "draft", "test_steps": []}
                        ],
                    },
                },
            )
            refs = [{"module": "procese", "folder": "AC001_test"}]

            with patch.object(type(library), "_iter_process_sources", lambda s: [("procese", tmp_repo)]):
                created = library.import_processes(refs, project=self.project)

        self.assertEqual(len(created), 1)
        proc = created[0]
        self.assertEqual(proc.code, "GITAC001")
        self.assertEqual(proc.name, "Achiziție Git")
        self.assertEqual(proc.project_id, self.project)
        self.assertEqual(len(proc.step_ids), 1)

    def test_repo_local_name(self):
        """_repo_local_name extrage corect numele folderului din URL."""
        library = self.env["business.process.library"]
        self.assertEqual(library._repo_local_name("https://github.com/terrabit-ro/procese"), "procese")
        self.assertEqual(library._repo_local_name("https://github.com/org/my-repo.git"), "my-repo")
        self.assertEqual(library._repo_local_name("git@github.com:org/repo.git"), "repo")
