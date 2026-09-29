#!/usr/bin/env python
# scripts/test_check_po_vs_pot.py
"""Teste pentru hook-ul check_po_vs_pot.py.

Ruleaza din radacina suitei:

    python3 -m unittest scripts/test_check_po_vs_pot.py

Scenariul de baza reproduce `git commit` dintr-un git worktree: git exporta
GIT_DIR catre hook-uri, iar hook-ul trebuie sa verifice tot DOAR intrarile
adaugate in commit, nu si termenii morti deja existenti in .po.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_po_vs_pot.py")

POT = """msgid ""
msgstr ""

msgid "Alive"
msgstr ""
"""

PO_VECHI = """msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Alive"
msgstr "Viu"

msgid "Dead"
msgstr "Mort"
"""

PO_NOU = (
    PO_VECHI
    + """
msgid "Fresh"
msgstr "Proaspat"
"""
)

# Hook minimal care ruleaza scriptul pe .po-urile din commit, ca pre-commit.
HOOK = f"""#!/bin/sh
files=$(git diff --cached --name-only --diff-filter=ACM -- '*.po')
[ -z "$files" ] && exit 0
exec "{sys.executable}" "{SCRIPT}" $files
"""


def git(cwd, *args, env=None):
    return subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True, check=True).stdout


def env_curat():
    """Mediul fara variabilele GIT_* mostenite (testul poate rula chiar dintr-un hook)."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


class TestCheckPoVsPot(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.env = env_curat()
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(self.repo, "modul", "i18n"))
        self.scrie(self.repo, "modul/i18n/modul.pot", POT)
        self.scrie(self.repo, "modul/i18n/ro.po", PO_VECHI)
        git(self.repo, "init", "-q", "-b", "main", env=self.env)
        git(self.repo, "config", "user.email", "test@example.com", env=self.env)
        git(self.repo, "config", "user.name", "Test", env=self.env)
        git(self.repo, "add", "modul", env=self.env)
        git(self.repo, "commit", "-q", "-m", "init", env=self.env)
        self.wt = os.path.join(self.tmp, "wt")
        git(self.repo, "worktree", "add", "-q", self.wt, "-b", "lucru", env=self.env)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        super().tearDown()

    @staticmethod
    def scrie(radacina, rel, continut):
        with open(os.path.join(radacina, rel), "w", encoding="utf-8") as f:
            f.write(continut)

    def ruleaza(self, cwd, env):
        return subprocess.run(
            [sys.executable, SCRIPT, "modul/i18n/ro.po"], cwd=cwd, env=env, capture_output=True, text=True
        )

    def test_worktree_cu_git_dir_ignora_termenii_morti_vechi(self):
        """Ca in `git commit` dintr-un worktree: GIT_DIR setat, fara GIT_WORK_TREE."""
        env = dict(self.env, GIT_DIR=git(self.wt, "rev-parse", "--git-dir", env=self.env).strip())
        rezultat = self.ruleaza(self.wt, env)
        self.assertEqual(rezultat.returncode, 0, rezultat.stderr)
        self.assertNotIn("Dead", rezultat.stderr)

    def test_worktree_cu_git_dir_prinde_intrarea_noua(self):
        self.scrie(self.wt, "modul/i18n/ro.po", PO_NOU)
        env = dict(self.env, GIT_DIR=git(self.wt, "rev-parse", "--git-dir", env=self.env).strip())
        rezultat = self.ruleaza(self.wt, env)
        self.assertEqual(rezultat.returncode, 1)
        self.assertIn("Fresh", rezultat.stderr)
        self.assertNotIn("Dead", rezultat.stderr)

    def test_git_commit_real_din_worktree(self):
        """Cap-coada: hook-ul rulat de `git commit` insusi, cu mediul pus de git."""
        hooks = os.path.join(self.tmp, "hooks")
        os.makedirs(hooks)
        cale_hook = os.path.join(hooks, "pre-commit")
        self.scrie(hooks, "pre-commit", HOOK)
        os.chmod(cale_hook, 0o755)
        git(self.repo, "config", "core.hooksPath", hooks, env=self.env)

        # Modificare fara termeni noi: commit-ul trebuie sa treaca, desi "Dead" lipseste din .pot.
        self.scrie(self.wt, "modul/i18n/ro.po", PO_VECHI.replace('"Viu"', '"Viu!"'))
        git(self.wt, "add", "modul/i18n/ro.po", env=self.env)
        rezultat = subprocess.run(
            ["git", "commit", "-q", "-m", "fara termeni noi"], cwd=self.wt, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(rezultat.returncode, 0, rezultat.stderr)

        # Termen nou absent din .pot: commit-ul trebuie blocat, doar pentru el.
        self.scrie(self.wt, "modul/i18n/ro.po", PO_NOU)
        git(self.wt, "add", "modul/i18n/ro.po", env=self.env)
        rezultat = subprocess.run(
            ["git", "commit", "-q", "-m", "termen nou"], cwd=self.wt, env=self.env, capture_output=True, text=True
        )
        self.assertNotEqual(rezultat.returncode, 0)
        self.assertIn("Fresh", rezultat.stderr)
        self.assertNotIn("Dead", rezultat.stderr)

    def test_fisier_nou_verifica_tot(self):
        """Un .po nou in commit nu are versiune in HEAD: se verifica integral."""
        os.makedirs(os.path.join(self.wt, "altul", "i18n"))
        self.scrie(self.wt, "altul/i18n/altul.pot", POT)
        self.scrie(self.wt, "altul/i18n/ro.po", PO_VECHI)
        rezultat = subprocess.run(
            [sys.executable, SCRIPT, "altul/i18n/ro.po"], cwd=self.wt, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(rezultat.returncode, 1)
        self.assertIn("Dead", rezultat.stderr)


if __name__ == "__main__":
    unittest.main()
