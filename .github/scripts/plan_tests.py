#!/usr/bin/env python3
"""Decide WHICH addons get tested and on HOW MANY parallel jobs.

Rules:

* pull_request / push -> only the addons touched by the diff, plus their
  transitive reverse dependents (a change in `deltatech` can break anything
  that depends on it). A change in a repo-root or dotdir file falls back to a
  full run.
* workflow_dispatch without input, or no usable base commit -> the whole repo.
* workflow_dispatch with `modules` -> exactly that list (no reverse expansion:
  a manual run is targeted by definition).

The selection is then split into shards by functional family. The split is not
only about parallelism: each family drags in its own Odoo core stack, so a
`website` shard installs website+sale but not mrp or pos. Roughly half of a
full run is spent installing modules, so keeping the stacks apart is what
actually shortens the job.

Writes to $GITHUB_OUTPUT:
    run_tests  true/false (false = nothing to test, the test job is skipped)
    full       true/false (true = whole repo; only then do we upload coverage)
    matrix     JSON for `strategy.matrix`

This runs in a plain `ubuntu-latest` job, NOT inside the OCA container: git
calls from inside the container could not resolve the base commit, so the old
inline version silently fell back to a full run on every single build.
"""

import ast
import json
import os
import subprocess
import sys

# Maximum addons per shard. Bigger families are cut into `name-1`, `name-2`, ...
# Do not lower this lightly: every shard pays the full fixed cost (container
# boot, addon install, test db init) of roughly 2.5 minutes, so many small
# shards buy wall-clock time with a lot of runner minutes.
MAX_PER_SHARD = 30

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


def group_of(name):
    """Functional family of an addon. New addons are placed automatically by prefix.

    Order matters: `deltatech_website_sale_*` is a website addon, not a sale one,
    so the website prefix has to be tested first.
    """
    # Prefixes are written WITHOUT a trailing underscore so that the bare addon
    # (`deltatech_mrp`, `deltatech_account`) lands in its own family too.
    families = (
        ("website", ("deltatech_website",)),
        ("pos", ("deltatech_pos",)),
        ("mrp", ("deltatech_mrp",)),
        ("account", ("deltatech_account", "deltatech_invoice", "deltatech_ledger")),
        ("purchase", ("deltatech_purchase", "deltatech_fast_purchase")),
        ("sale", ("deltatech_sale", "deltatech_saleorder", "deltatech_fast_sale")),
        ("stock", ("deltatech_stock", "deltatech_picking", "deltatech_warehouse", "deltatech_product")),
    )
    for family, prefixes in families:
        if name.startswith(prefixes):
            return family
    return "misc"


def build_matrix(modules):
    """Split the addons into shards: group by family, then cut at MAX_PER_SHARD."""
    groups = {}
    for name in sorted(modules):
        groups.setdefault(group_of(name), []).append(name)

    shards = []
    # Stable order, so job names do not dance from one run to the next.
    for group in sorted(groups):
        members = groups[group]
        # BALANCED cut, not greedy fill: 31 addons give 16+15, not 30+1. A shard
        # with a single addon pays the whole fixed cost for almost no work.
        count = -(-len(members) // MAX_PER_SHARD)  # ceil
        chunks = [members[index::count] for index in range(count)]
        for index, chunk in enumerate(chunks, start=1):
            shard_name = group if len(chunks) == 1 else f"{group}-{index}"
            shards.append({"name": shard_name, "modules": ",".join(chunk)})
    return shards


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


def emit(run_tests, full, shards):
    lines = [
        f"run_tests={'true' if run_tests else 'false'}",
        f"full={'true' if full else 'false'}",
        f"matrix={json.dumps({'include': shards})}",
    ]
    for line in lines:
        print(line)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")


def select(manifests):
    """Return (selected_addons, full) for the current event."""
    event = os.environ.get("EVENT_NAME", "")
    requested = os.environ.get("INPUT_MODULES", "").strip()
    base_sha = os.environ.get("BASE_SHA", "")
    head_sha = os.environ.get("HEAD_SHA", "") or "HEAD"

    if requested:
        # Targeted manual run: exactly what was asked for, no reverse expansion.
        selection = {name.strip() for name in requested.split(",") if name.strip()}
        unknown = selection - set(manifests)
        if unknown:
            print(f"::error::Addons not found in this repo: {', '.join(sorted(unknown))}")
            sys.exit(1)
        return selection, False

    if event not in ("pull_request", "push"):
        print(f"Event {event!r} -> full run.")
        return set(manifests), True
    if not usable(base_sha):
        print(f"Base commit {base_sha!r} not available -> full run.")
        return set(manifests), True

    touched = changed_addons(manifests, base_sha, head_sha)
    if touched is None:
        return set(manifests), True

    selection = reverse_dependents(manifests, touched)
    print(f"Touched addons: {', '.join(sorted(touched)) or '(none)'}")
    extra = selection - touched
    if extra:
        print(f"Reverse dependents added: {', '.join(sorted(extra))}")
    if len(selection) == len(manifests):
        print("Every addon is affected -> full run.")
        return selection, True
    return selection, False


def main():
    manifests = load_manifests()
    selection, full = select(manifests)

    shards = build_matrix(selection)
    if not shards:
        # Only non-addon content changed (docs, images outside any addon).
        print("No addon affected, nothing to test.")
        emit(False, full, [])
        return 0

    print(f"{len(selection)} addons in {len(shards)} shards:")
    for shard in shards:
        print(f"  {shard['name']}: {len(shard['modules'].split(','))} addons")
    emit(True, full, shards)
    return 0


if __name__ == "__main__":
    sys.exit(main())
