#!/usr/bin/env python3
"""Check that each modified Odoo addon has a readme/HISTORY.md file
and that the manifest version is mentioned in it."""

import argparse
import ast
import logging
import re
import sys
from pathlib import Path

_logger = logging.getLogger(__name__)


def find_addon_root(file_path: Path, repo_root: Path) -> Path | None:
    """Return the addon root directory for a given file, or None."""
    for candidate in file_path.parents:
        if (candidate / "__manifest__.py").exists():
            try:
                rel = candidate.relative_to(repo_root)
                if len(rel.parts) == 1:
                    return candidate
            except ValueError:
                _logger.debug("Candidate %s is not relative to repo root", candidate)
    return None


def get_manifest_version(addon: Path) -> str | None:
    """Return the version string from __manifest__.py, or None."""
    manifest_path = addon / "__manifest__.py"
    try:
        tree = ast.literal_eval(manifest_path.read_text(encoding="utf-8"))
        return tree.get("version")
    except Exception as exc:
        _logger.debug("Could not read manifest version from %s: %s", manifest_path, exc)
        return None


def check_version_in_history(history_path: Path, version: str) -> bool:
    """Return True if version appears as a markdown heading in HISTORY.md."""
    content = history_path.read_text(encoding="utf-8")
    # Match lines like: ## 18.0.2.2.2 or ## 18.0.2.2.2 (2026-04-28)
    pattern = re.compile(r"^#{1,3}\s+" + re.escape(version) + r"(\s|$)", re.MULTILINE)
    return bool(pattern.search(content))


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--error",
        action="store_true",
        default=False,
        help="Return exit code 1 (error) instead of 0 (warning) when checks fail.",
    )
    args, file_args = parser.parse_known_args()

    repo_root = Path.cwd()
    checked = set()
    has_issues = False

    for arg in file_args:
        file_path = Path(arg).resolve()
        addon = find_addon_root(file_path, repo_root)
        if addon is None:
            continue
        addon_rel = str(addon.relative_to(repo_root))
        if addon_rel in checked:
            continue
        checked.add(addon_rel)

        history = addon / "readme" / "HISTORY.md"
        if not history.exists():
            _logger.warning("WARNING: %s — lipsește readme/HISTORY.md", addon_rel)
            has_issues = True
            continue

        version = get_manifest_version(addon)
        if not version:
            _logger.warning("WARNING: %s — nu s-a putut citi versiunea din __manifest__.py", addon_rel)
            has_issues = True
            continue

        if not check_version_in_history(history, version):
            _logger.warning(
                "WARNING: %s — versiunea %s din manifest nu apare în readme/HISTORY.md",
                addon_rel,
                version,
            )
            has_issues = True

    return 1 if (args.error and has_issues) else 0


if __name__ == "__main__":
    sys.exit(main())
