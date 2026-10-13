#!/usr/bin/env python
# scripts/check_module_images.py
"""Asigura faptul ca fiecare modul Odoo are o captura declarata in 'images'.

Pentru fiecare __manifest__.py instalabil:
- daca lipseste cheia 'images', o adauga pointand catre
  static/description/main_screenshot.png;
- daca fisierul main_screenshot.png lipseste, este preluat automat din modulul
  `deltatech` (captura generica), la fel ca iconita.

Daca un modul listeaza in 'images' alte fisiere decat main_screenshot.png si
acestea lipsesc, hook-ul raporteaza (nu poate inventa capturi specifice).

Hook-ul iese cu cod non-zero atunci cand a modificat fisiere, pentru ca
utilizatorul sa le verifice si sa le adauge in commit. Modulele neinstalabile
(installable=False) sunt ignorate.
"""

import ast
import os
import shutil
import sys

DESCRIPTION_REL_DIR = os.path.join("static", "description")
DEFAULT_IMAGE = os.path.join(DESCRIPTION_REL_DIR, "main_screenshot.png")
DEFAULT_IMAGE_POSIX = DEFAULT_IMAGE.replace(os.sep, "/")
SOURCE_MODULE = "deltatech"


def repo_root():
    # scripts/ se afla in radacina repo-ului
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_manifest(manifest_path):
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return ast.literal_eval(f.read())
    except (SyntaxError, ValueError):
        # Lasam alte hook-uri sa raporteze manifestul invalid
        return None


def add_images_key(manifest_path):
    """Insereaza cheia 'images' dupa acolada de deschidere a dict-ului."""
    with open(manifest_path, encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.strip() == "{":
            lines.insert(i + 1, f'    "images": ["{DEFAULT_IMAGE_POSIX}"],\n')
            break
    else:
        return False
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True


def main(argv):
    source_image = os.path.join(repo_root(), SOURCE_MODULE, DEFAULT_IMAGE)
    changed = []
    errors = []

    for manifest_path in argv:
        if os.path.basename(manifest_path) != "__manifest__.py":
            continue
        manifest = read_manifest(manifest_path)
        if manifest is None:
            continue
        if not manifest.get("installable", True):
            continue

        module_dir = os.path.dirname(manifest_path)
        # Nu modificam modulul sursa
        if os.path.basename(os.path.abspath(module_dir)) == SOURCE_MODULE:
            continue

        images = manifest.get("images")

        # 1. Adauga cheia 'images' daca lipseste
        if not images:
            if add_images_key(manifest_path):
                changed.append((module_dir, f"adaugata cheia 'images' -> {DEFAULT_IMAGE_POSIX}"))
                images = [DEFAULT_IMAGE_POSIX]
            else:
                errors.append((module_dir, "nu s-a putut adauga cheia 'images'"))
                continue

        # 2. Asigura existenta fisierelor listate
        for image in images:
            image_path = os.path.join(module_dir, image)
            if os.path.exists(image_path):
                continue
            # Preia captura generica doar pentru main_screenshot.png
            if os.path.basename(image) == "main_screenshot.png":
                if not os.path.exists(source_image):
                    errors.append((module_dir, f"lipseste sursa {SOURCE_MODULE}/{DEFAULT_IMAGE_POSIX}"))
                    continue
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                shutil.copyfile(source_image, image_path)
                changed.append((module_dir, f"captura preluata din {SOURCE_MODULE}: {image}"))
            else:
                errors.append((module_dir, f"fisierul lipseste (captura specifica): {image}"))

    if changed:
        print("Imagini completate automat:")
        for module_dir, msg in changed:
            print(f"  + {module_dir}: {msg}")
        print("\nVerificati modificarile si adaugati-le in commit (git add).")

    if errors:
        print("\nProbleme nerezolvabile automat:")
        for module_dir, msg in errors:
            print(f"  - {module_dir}: {msg}")

    return 1 if (changed or errors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
