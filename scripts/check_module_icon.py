#!/usr/bin/env python
# scripts/check_module_icon.py
"""Verifica faptul ca fiecare modul Odoo are o iconita.

Pentru fiecare __manifest__.py primit ca argument, scriptul verifica existenta
fisierului static/description/icon.png in directorul modulului. Modulele
neinstalabile (installable=False) sunt ignorate.
"""

import ast
import os
import sys

ICON_REL_PATH = os.path.join("static", "description", "icon.png")


def is_installable(manifest_path):
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = ast.literal_eval(f.read())
    except (SyntaxError, ValueError):
        # Lasam alte hook-uri sa raporteze manifestul invalid
        return False
    return bool(manifest.get("installable", True))


def main(argv):
    missing = []
    for manifest_path in argv:
        if os.path.basename(manifest_path) != "__manifest__.py":
            continue
        if not is_installable(manifest_path):
            continue
        module_dir = os.path.dirname(manifest_path)
        icon_path = os.path.join(module_dir, ICON_REL_PATH)
        if not os.path.exists(icon_path):
            missing.append(module_dir)

    if missing:
        print("Urmatoarele module nu au iconita (static/description/icon.png):")
        for module_dir in missing:
            print(f"  - {module_dir}")
        print(
            "\nAdaugati o iconita PNG la calea de mai sus pentru fiecare modul "
            "(ex: copiati static/description/icon.png dintr-un modul existent)."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
