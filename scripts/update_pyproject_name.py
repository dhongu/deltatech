#!/usr/bin/env python
# scripts/update_pyproject_name.py
import ast
import logging
import os

import tomli
import tomli_w

_logger = logging.getLogger(__name__)


def update_name(filename):
    """Citeste numele modulului din __manifest__.py si actualizeaza pyproject.toml."""
    module_dir = os.path.dirname(filename)
    manifest_path = os.path.join(module_dir, "__manifest__.py")

    if not os.path.exists(manifest_path):
        return

    # 1. Citeste numele din __manifest__.py
    with open(manifest_path, encoding="utf-8") as f:
        ast.literal_eval(f.read())

    # Numele pachetului va fi numele directorului modulului, sau 'name' din manifest,
    # conform conventiei OCA (ex: 'odoo-addon-nume_modul')
    # Folosim numele directorului, care este numele Odoo al modulului
    module_name = os.path.basename(module_dir)
    package_name = f"odoo-addon-{module_name.replace('_', '-')}"

    # 2. Citeste pyproject.toml
    try:
        with open(filename, "rb") as f:
            data = tomli.load(f)
    except FileNotFoundError:
        data = {}

    # 3. Actualizeaza cheia [project].name
    if "project" not in data:
        data["project"] = {}

    if data["project"].get("name") != package_name:
        data["project"]["name"] = package_name

        # 4. Scrie inapoi in pyproject.toml
        with open(filename, "wb") as f:
            tomli_w.dump(data, f)
        _logger.info(f"Updated name in {filename} to {package_name}")


def find_all_pyproject_files(root_dir="."):
    """Gaseste toate fisierele pyproject.toml din subdirectoare."""
    pyproject_files = []
    # Parcurge directorul incepand de la root_dir (care este directorul radacina al repo-ului)
    for dirpath, _dirnames, filenames in os.walk(root_dir):
        # Ignora directoarele care nu sunt module Odoo sau directoarele ascunse/build
        if "pyproject.toml" in filenames and os.path.basename(dirpath) != ".":
            pyproject_files.append(os.path.join(dirpath, "pyproject.toml"))
    return pyproject_files


_logger.info("Updating pyproject.toml files with correct names...")

if __name__ == "__main__":
    # Acum, scriptul gaseste singur toate fisierele, indiferent de commit
    all_files = find_all_pyproject_files()
    _logger.info(f"Found {len(all_files)} pyproject.toml files")
    for filename in all_files:
        update_name(filename)
