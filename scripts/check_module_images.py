#!/usr/bin/env python
# scripts/check_module_images.py
"""Verifica faptul ca fiecare modul Odoo declara cheia 'images' in manifest.

Pentru fiecare __manifest__.py primit ca argument:
- manifestul instalabil trebuie sa declare cheia 'images' cu cel putin un fisier;
- fiecare fisier listat in 'images' trebuie sa existe pe disc.

Spre deosebire de iconita, captura (main_screenshot.png) este specifica fiecarui
modul, deci NU se copiaza automat - hook-ul doar raporteaza si blocheaza commit-ul.
Modulele neinstalabile (installable=False) sunt ignorate.
"""

import ast
import os
import sys


def read_manifest(manifest_path):
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return ast.literal_eval(f.read())
    except (SyntaxError, ValueError):
        # Lasam alte hook-uri sa raporteze manifestul invalid
        return None


def main(argv):
    problems = []

    for manifest_path in argv:
        if os.path.basename(manifest_path) != "__manifest__.py":
            continue
        manifest = read_manifest(manifest_path)
        if manifest is None:
            continue
        if not manifest.get("installable", True):
            continue

        module_dir = os.path.dirname(manifest_path)
        images = manifest.get("images")

        if not images:
            problems.append((module_dir, "lipseste cheia 'images' in manifest"))
            continue

        for image in images:
            image_path = os.path.join(module_dir, image)
            if not os.path.exists(image_path):
                problems.append((module_dir, f"fisierul lipseste: {image}"))

    if problems:
        print("Probleme cu cheia 'images' (ex: static/description/main_screenshot.png):")
        for module_dir, msg in problems:
            print(f"  - {module_dir}: {msg}")
        print(
            "\nAdaugati in __manifest__.py cheia:\n"
            '    "images": ["static/description/main_screenshot.png"],\n'
            "si o captura reprezentativa pentru modul la calea respectiva."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
