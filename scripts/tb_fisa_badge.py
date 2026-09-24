#!/usr/bin/env python3
# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Adaugă badge-ul „Fișă consultant” în README.rst la modulele care au fișă.

README.rst e generat de ``oca-gen-addon-readme``, al cărui șablon nu vede fișierele din
``readme/``: primește doar fragmentele dintr-o listă fixă. De aceea badge-ul se pune după
generare, de acest script, rulat ca hook manual după ``oca-gen-addon-readme``.

Pentru fiecare modul din ``--addons-dir``:

- dacă are ``readme/FISA_CONSULTANT.md``, README.rst primește lângă celelalte badge-uri
  ``|badge_fisa|``, cu link la fișa de pe GitHub;
- dacă nu are (sau fișa a fost ștearsă), badge-ul e scos.

Idempotent: o a doua rulare nu schimbă nimic. Modulele fără README.rst, sau cu un README
fără linia de badge-uri generată, sunt lăsate neatinse.

Rulare::

    python3 scripts/tb_fisa_badge.py --addons-dir=.
"""

import argparse
import os
import re
import subprocess
import sys

FISA_PATH = os.path.join("readme", "FISA_CONSULTANT.md")
IMAGE = "https://img.shields.io/badge/-Fi%C8%99%C4%83%20consultant-2ea44f.png"
ALT = "Fișă consultant"
TOKEN = "|badge_fisa|"
DEFINITION_START = ".. |badge_fisa| image::"
# linia generată de oca-gen-addon-readme: |badge1| |badge2| ..., eventual cu badge-ul nostru
BADGES_LINE = re.compile(r"^\|badge\d+\|( \|badge\d+\|)*( \|badge_fisa\|)?$")


def repo_from_git(addons_dir):
    """(org, repo) din remote-ul origin, ca linkul să urmeze repo-ul real al suitei."""
    try:
        url = subprocess.check_output(
            ["git", "-C", addons_dir, "remote", "get-url", "origin"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None, None
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
    return (match.group(1), match.group(2)) if match else (None, None)


def strip_badge(lines):
    """Scoate definiția și tokenul badge-ului, oriunde ar fi."""
    result = []
    skipping = False
    for line in lines:
        if line.startswith(DEFINITION_START):
            skipping = True
            continue
        if skipping and line.startswith("    :"):
            continue
        skipping = False
        if BADGES_LINE.match(line) and line.endswith(" " + TOKEN):
            line = line[: -len(" " + TOKEN)]
        result.append(line)
    return result


def add_badge(lines, target):
    """Pune definiția înaintea liniei de badge-uri și tokenul la capătul ei."""
    index = next((i for i, line in enumerate(lines) if BADGES_LINE.match(line)), None)
    if index is None:
        return None
    definition = [f"{DEFINITION_START} {IMAGE}", f"    :target: {target}", f"    :alt: {ALT}"]
    # definițiile generate sunt urmate de o linie goală, apoi linia de badge-uri
    insert_at = index - 1 if index and not lines[index - 1].strip() else index
    lines = lines[:insert_at] + definition + lines[insert_at:]
    badges_index = index + len(definition)
    lines[badges_index] = lines[badges_index] + " " + TOKEN
    return lines


def process_addon(addon_dir, addon_name, org, repo, branch):
    readme = os.path.join(addon_dir, "README.rst")
    if not os.path.isfile(readme):
        return False
    with open(readme, encoding="utf8") as f:
        original = f.read()
    lines = strip_badge(original.split("\n"))
    if os.path.isfile(os.path.join(addon_dir, FISA_PATH)):
        target = f"https://github.com/{org}/{repo}/blob/{branch}/{addon_name}/readme/FISA_CONSULTANT.md"
        with_badge = add_badge(lines, target)
        if with_badge is None:
            sys.stderr.write(f"{addon_name}: README.rst fără linie de badge-uri, sărit\n")
            return False
        lines = with_badge
    content = "\n".join(lines)
    if content == original:
        return False
    with open(readme, "w", encoding="utf8") as f:
        f.write(content)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--addons-dir", default=".")
    parser.add_argument("--org", help="organizația GitHub (implicit: din remote-ul origin)")
    parser.add_argument("--repo", help="repo-ul GitHub (implicit: din remote-ul origin)")
    parser.add_argument("--branch", default="19.0")
    args = parser.parse_args()

    org, repo = args.org, args.repo
    if not (org and repo):
        git_org, git_repo = repo_from_git(args.addons_dir)
        org, repo = org or git_org, repo or git_repo
    if not (org and repo):
        parser.error("nu pot determina repo-ul GitHub: dați --org și --repo")

    changed = []
    for name in sorted(os.listdir(args.addons_dir)):
        addon_dir = os.path.join(args.addons_dir, name)
        if os.path.isfile(os.path.join(addon_dir, "__manifest__.py")):
            if process_addon(addon_dir, name, org, repo, args.branch):
                changed.append(name)
    for name in changed:
        sys.stdout.write(f"{name}: badge „Fișă consultant” actualizat\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
