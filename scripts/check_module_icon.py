#!/usr/bin/env python
# scripts/check_module_icon.py
"""Asigura faptul ca fiecare modul Odoo are o iconita.

Pentru fiecare __manifest__.py primit ca argument, scriptul verifica existenta
fisierului static/description/icon.png in directorul modulului. Daca lipseste,
iconita (icon.png si icon.svg) este preluata automat din modulul `deltatech`.
Modulele neinstalabile (installable=False) sunt ignorate.

Hook-ul iese cu cod non-zero atunci cand a copiat fisiere, pentru ca
utilizatorul sa le verifice si sa le adauge in commit (conventie pre-commit
pentru hook-urile care modifica fisiere).
"""

import ast
import os
import shutil
import sys

ICON_FILES = ("icon.png", "icon.svg")
DESCRIPTION_REL_DIR = os.path.join("static", "description")
SOURCE_MODULE = "deltatech"


def repo_root():
    # scripts/ se afla in radacina repo-ului
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_installable(manifest_path):
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = ast.literal_eval(f.read())
    except (SyntaxError, ValueError):
        # Lasam alte hook-uri sa raporteze manifestul invalid
        return False
    return bool(manifest.get("installable", True))


def main(argv):
    source_dir = os.path.join(repo_root(), SOURCE_MODULE, DESCRIPTION_REL_DIR)
    copied = []
    errors = []

    for manifest_path in argv:
        if os.path.basename(manifest_path) != "__manifest__.py":
            continue
        if not is_installable(manifest_path):
            continue
        module_dir = os.path.dirname(manifest_path)
        # Nu copiem peste modulul sursa
        if os.path.basename(os.path.abspath(module_dir)) == SOURCE_MODULE:
            continue

        dest_dir = os.path.join(module_dir, DESCRIPTION_REL_DIR)
        icon_path = os.path.join(dest_dir, "icon.png")
        if os.path.exists(icon_path):
            continue

        os.makedirs(dest_dir, exist_ok=True)
        for icon in ICON_FILES:
            src = os.path.join(source_dir, icon)
            dst = os.path.join(dest_dir, icon)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copyfile(src, dst)
                copied.append(dst)
        if not os.path.exists(icon_path):
            errors.append(module_dir)

    if copied:
        print("Iconite preluate automat din modulul 'deltatech':")
        for dst in copied:
            print(f"  + {dst}")
        print("\nVerificati iconitele si adaugati-le in commit (git add).")

    if errors:
        print(f"\nNu s-a putut prelua iconita pentru (lipseste sursa {SOURCE_MODULE}/{DESCRIPTION_REL_DIR}/icon.png?):")
        for module_dir in errors:
            print(f"  - {module_dir}")

    return 1 if (copied or errors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
