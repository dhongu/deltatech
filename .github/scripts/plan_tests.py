#!/usr/bin/env python3
"""Decide which addons the test job has to install and test.

Rules:

* pull_request / push -> only the addons touched by the diff, plus their
  transitive reverse dependents (a change in `deltatech` can break anything
  that depends on it). A change in a repo-root or dotdir file falls back to a
  full run.
* workflow_dispatch, or no usable base commit -> the whole repo.

Writes to $GITHUB_OUTPUT:
    addons     comma-separated list for INCLUDE ("" = whole repo)
    full       true/false (true = whole repo; only then do we upload coverage)

This runs in a plain `ubuntu-latest` job, NOT inside the OCA container: git
calls from inside the container could not resolve the base commit, so the old
inline version silently fell back to a full run on every single build.
"""

import ast
import os
import subprocess
import sys

# Root files that can affect every addon: filtering makes no sense for them.
INFRA_PREFIXES = (
    ".github/",
    "requirements.txt",
    "test-requirements.txt",
    ".pre-commit-config.yaml",
    ".ruff.toml",
    ".flake8",
    ".pylintrc",
    "setup/",
)


def load_manifests():
    """Return {addon_name: manifest_dict} for the addons at the repo root."""
    manifests = {}
    for entry in sorted(os.listdir(".")):
        path = os.path.join(entry, "__manifest__.py")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as handle:
            try:
                manifests[entry] = ast.literal_eval(handle.read())
            except (SyntaxError, ValueError) as err:
                # An unreadable manifest must not silently shrink the test
                # selection: report it and treat the addon as dependency-less.
                print(f"::warning file={path}::unreadable manifest: {err}", file=sys.stderr)
                manifests[entry] = {}
    return manifests


def reverse_dependents(manifests, seeds):
    """Transitive closure of dependents: what `seeds` could break."""
    dependents = {name: set() for name in manifests}
    for name, manifest in manifests.items():
        for dep in manifest.get("depends", []):
            if dep in dependents:
                dependents[dep].add(name)

    selected = set(seeds)
    queue = list(seeds)
    while queue:
        current = queue.pop()
        for child in dependents.get(current, ()):
            if child not in selected:
                selected.add(child)
                queue.append(child)
    return selected


def usable(sha):
    if not sha or set(sha) == {"0"}:
        return False
    return subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"]).returncode == 0


def changed_addons(manifests, base_sha, head_sha):
    """Addons touched by the diff, or None when infrastructure changed."""
    diff = subprocess.run(
        ["git", "diff", "--name-only", base_sha, head_sha],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    touched = set()
    for path in diff:
        if path.startswith(INFRA_PREFIXES):
            print(f"Infrastructure file changed ({path}) -> full run.")
            return None
        top = path.split("/", 1)[0]
        if top == path:
            print(f"Repo-root file changed ({path}) -> full run.")
            return None
        # Deleted addons have no manifest left; there is nothing to test.
        if top in manifests:
            touched.add(top)
    return touched


def emit(addons, full):
    lines = [
        f"addons={','.join(sorted(addons))}",
        f"full={'true' if full else 'false'}",
    ]
    for line in lines:
        print(line)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")


def main():
    manifests = load_manifests()
    event = os.environ.get("EVENT_NAME", "")
    base_sha = os.environ.get("BASE_SHA", "")
    head_sha = os.environ.get("HEAD_SHA", "") or "HEAD"

    if event not in ("pull_request", "push"):
        print(f"Event {event!r} -> full run.")
        emit([], True)
        return 0
    if not usable(base_sha):
        print(f"Base commit {base_sha!r} not available -> full run.")
        emit([], True)
        return 0

    touched = changed_addons(manifests, base_sha, head_sha)
    if touched is None:
        emit([], True)
        return 0

    selection = reverse_dependents(manifests, touched)
    print(f"Touched addons: {', '.join(sorted(touched)) or '(none)'}")
    extra = selection - touched
    if extra:
        print(f"Reverse dependents added: {', '.join(sorted(extra))}")

    if not selection:
        # Only non-addon content (docs, images inside no addon) changed. An
        # empty INCLUDE means "everything" for the OCA tooling, so pick a
        # single cheap addon instead of accidentally running the whole repo.
        print("No addon affected -> testing `deltatech` alone as a smoke check.")
        if "deltatech" in manifests:
            emit(["deltatech"], False)
        else:
            emit([], True)
        return 0

    if len(selection) == len(manifests):
        print("Every addon is affected -> full run.")
        emit([], True)
        return 0

    print(f"{len(selection)} addons selected out of {len(manifests)}.")
    emit(selection, False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
