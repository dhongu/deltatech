#!/usr/bin/env python3
# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Scrie ``scripts/test_stats.json``: numărul de teste și acoperirea de cod pe fiecare modul.

SURSA CANONICĂ: odoo-addons/bitshop/scripts/tb_test_stats.py. Celelalte suite țin o copie
identică, sincronizată împreună cu tb_gen_index.py de ``bitshop/scripts/tb_sync_gen_index.py``.

``tb_gen_index.py`` citește fișierul și pune în antetul paginii de pe Apps Store badge-ul
„N automated tests · X% coverage”. Badge-ul e text static în ``index.html``, nu o imagine
live de pe Codecov: store-ul arată versiunea publicată a modulului, deci cifra trebuie să
fie a acelei versiuni. Iar o imagine live ar putea arăta oricând „unknown” sau o cifră
dintr-o rulare ratată.

Surse:

- **testele** se numără static, din ``<modul>/tests/**/*.py``: metodele ``test*`` din
  clase, adică exact ce descoperă runner-ul Odoo. Nu e nevoie de CI.
- **acoperirea** vine din API-ul Codecov, pe ultimul commit al branch-ului. La un repo
  public merge fără token; la unul privat API-ul răspunde 404 fără token, deci scriptul
  citește ``CODECOV_API_TOKEN`` din mediu (token personal din Codecov, Settings → Access,
  nu tokenul de upload din CI). Fără acoperire disponibilă, scrie doar numărul de teste. Raportul îl urcă rularea completă de noapte din
  ``.github/workflows/test.yml``, iar fișierele ``tests/`` sunt excluse din el prin
  ``codecov.yml``. Acoperirea unui modul = liniile atinse / liniile măsurate, adunate pe
  toate fișierele lui. O linie parțial atinsă (ramură neexecutată) nu se numără ca
  atinsă, ca în Codecov.

Rulare (din rădăcina suitei)::

    python3 scripts/tb_test_stats.py                 # Codecov + numărarea testelor
    python3 scripts/tb_test_stats.py --no-coverage   # doar testele, fără rețea
    python3 scripts/tb_gen_index.py --addons-dir=.   # apoi regenerează paginile
"""

import argparse
import ast
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

OUTPUT = os.path.join("scripts", "test_stats.json")
CODECOV_API = "https://api.codecov.io/api/v2/github/%(owner)s/repos/%(repo)s/totals/?branch=%(branch)s"


def find_addons(addons_dir):
    for entry in sorted(os.listdir(addons_dir)):
        d = os.path.join(addons_dir, entry)
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "__manifest__.py")):
            yield entry


def count_tests(addon_dir):
    """Metodele ``test*`` din clasele modulelor ``tests/``, ca la descoperirea unittest."""
    tests_dir = os.path.join(addon_dir, "tests")
    total = 0
    for root, _dirs, files in os.walk(tests_dir):
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf8") as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    total += sum(
                        1
                        for item in node.body
                        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name.startswith("test")
                    )
    return total


def repo_from_git(addons_dir):
    """(owner, repo) din remote-ul origin: git@github.com:dhongu/deltatech.git."""
    url = subprocess.run(
        ["git", "-C", addons_dir, "remote", "get-url", "origin"], capture_output=True, text=True, check=True
    ).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not m:
        sys.exit(f"Remote-ul origin nu e pe GitHub: {url}")
    return m.group(1), m.group(2)


def fetch_codecov(owner, repo, branch):
    """Raportul Codecov al branch-ului, sau None dacă nu e accesibil (repo privat fără token)."""
    url = CODECOV_API % dict(owner=owner, repo=repo, branch=branch)
    request = urllib.request.Request(url)
    token = os.environ.get("CODECOV_API_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        hint = "" if token else " (repo privat? setează CODECOV_API_TOKEN)"
        sys.stderr.write(f"Codecov {owner}/{repo}@{branch}: HTTP {err.code}{hint}; scriu doar numărul de teste\n")
        return None


def coverage_by_addon(report, addons):
    """{modul: (linii măsurate, linii atinse)} din lista de fișiere a raportului."""
    totals = {}
    for item in report.get("files", []):
        addon, _sep, rest = item["name"].partition("/")
        if addon not in addons or rest.startswith("tests/") or "/tests/" in rest:
            continue
        lines, hits = totals.get(addon, (0, 0))
        totals[addon] = (lines + item["totals"]["lines"], hits + item["totals"]["hits"])
    return totals


def commit_from_report(report):
    m = re.search(r"/commit/([0-9a-f]{7,40})/", report.get("commit_file_url") or "")
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(description="Teste și acoperire pe modul → scripts/test_stats.json")
    ap.add_argument("--addons-dir", default=".", help="rădăcina suitei (implicit: directorul curent)")
    ap.add_argument("--branch", default="19.0", help="branch-ul din Codecov (implicit: 19.0)")
    ap.add_argument("--repo", help="owner/repo pe GitHub (implicit: din remote-ul origin)")
    ap.add_argument("--no-coverage", action="store_true", help="fără Codecov: doar numărul de teste")
    args = ap.parse_args()

    addons_dir = os.path.abspath(args.addons_dir)
    addons = list(find_addons(addons_dir))
    data = {
        "generated": datetime.date.today().isoformat(),
        "branch": args.branch,
        "addons": {},
    }

    coverage = {}
    if not args.no_coverage:
        owner, repo = args.repo.split("/", 1) if args.repo else repo_from_git(addons_dir)
        report = fetch_codecov(owner, repo, args.branch)
        if report:
            coverage = coverage_by_addon(report, set(addons))
            data["source"] = f"codecov:{owner}/{repo}"
            data["commit"] = commit_from_report(report)

    for addon in addons:
        entry = {"tests": count_tests(os.path.join(addons_dir, addon))}
        lines, hits = coverage.get(addon, (0, 0))
        if lines:
            entry["lines"] = lines
            entry["coverage"] = round(100.0 * hits / lines, 1)
        data["addons"][addon] = entry

    path = os.path.join(addons_dir, OUTPUT)
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")

    tested = sum(1 for e in data["addons"].values() if e["tests"])
    sys.stdout.write(f"{path}: {len(addons)} module, {tested} cu teste, {len(coverage)} cu acoperire\n")


if __name__ == "__main__":
    main()
