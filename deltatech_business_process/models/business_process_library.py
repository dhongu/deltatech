# ©  2023 Deltatech
# See README.rst file on addons root folder for license details
"""Generic engine for the process library (processes/*/process.json).

**Any installed module** that ships a ``processes/`` folder (with the standard
layout ``<folder>/process.json`` + optional ``fisa.html`` and
``screenshots/*.png``) contributes processes, discovered automatically. The base
module ``deltatech_business_process`` is only the engine — the content comes from
other modules (e.g. ``l10n_ro_process_library`` for Romania).

Processes are listed from disk and imported **selectively** into a project (they
are not auto-loaded on install).

Discovery is controlled from Settings (``ir.config_parameter``):

* ``deltatech_business_process.process_library_autodiscover`` (``"1"``/``"0"``,
  default ``"1"``) — scan every installed module that has a ``processes/`` folder;
  off = only the whitelisted modules.
* ``deltatech_business_process.process_library_whitelist`` (comma-separated list
  of modules) — when set, restrict the sources to exactly the listed modules.
* ``deltatech_business_process.process_library_git_repos`` (comma-separated list
  of git URLs) — additional sources cloned/pulled under the Odoo data dir.
  Repos are discovered with root layout ``<folder>/process.json`` (standalone repo,
  no ``processes/`` sub-folder needed).

Private HTTPS repos are supported via two optional parameters:

* ``deltatech_business_process.process_library_git_token`` — a personal access
  token / password sent as an HTTP Basic ``Authorization`` header per git
  command. It is **not** written into the repo's on-disk config.
* ``deltatech_business_process.process_library_git_user`` — the matching
  username (default ``x-access-token``, which works for GitHub tokens; use
  ``oauth2`` for GitLab). URLs that already embed credentials, and ``ssh://`` /
  ``git@`` URLs, are used as-is and ignore these parameters.
"""

import base64
import json
import logging
import os
import subprocess

from odoo import api, models, tools
from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)


class BusinessProcessLibrary(models.AbstractModel):
    _name = "business.process.library"
    _description = "Process Library (engine)"

    @api.model
    def _module_processes_dir(self, module_name):
        """Path of a module's ``processes/`` folder, or None if missing."""
        path = get_module_path(module_name)
        if not path:
            return None
        base = os.path.join(path, "processes")
        return base if os.path.isdir(base) else None

    @api.model
    def _git_repos_cache_dir(self):
        """Local directory where git repos are cloned (under Odoo data_dir)."""
        return os.path.join(tools.config.get("data_dir", os.path.expanduser("~/.local/share/Odoo")), "process_repos")

    @api.model
    def _repo_local_name(self, url):
        """Derive a filesystem-safe folder name from a git URL."""
        name = url.rstrip("/").rsplit("/", 1)[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name

    @api.model
    def _safe_url(self, url):
        """URL with any embedded ``user:pass@`` credentials stripped, for logging."""
        if "://" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                return f"{scheme}://{rest.split('@', 1)[1]}"
        return url

    @api.model
    def _git_env(self):
        """Non-interactive git environment so a missing/wrong credential fails fast.

        Without this, ``git`` would block on an interactive username/password (or
        SSH passphrase) prompt until the subprocess timeout (60-120s) elapses.
        """
        return dict(
            os.environ,
            GIT_TERMINAL_PROMPT="0",
            GIT_SSH_COMMAND="ssh -o BatchMode=yes",
        )

    @api.model
    def _git_auth_args(self, url):
        """Per-command ``-c http.extraHeader`` args injecting a token for private HTTPS repos.

        Returns ``[]`` for non-HTTPS URLs (ssh/git/file), URLs that already embed
        credentials, or when no token is configured. The token is supplied as an
        HTTP Basic header on the command line, so it is never persisted into the
        cloned repo's ``.git/config``.
        """
        if not url.startswith("https://"):
            return []
        authority = url.split("://", 1)[1].split("/", 1)[0]
        if "@" in authority:  # credentials already embedded in the URL — leave as-is
            return []
        icp = self.env["ir.config_parameter"].sudo()
        token = (icp.get_param("deltatech_business_process.process_library_git_token") or "").strip()
        if not token:
            return []
        user = (icp.get_param("deltatech_business_process.process_library_git_user") or "x-access-token").strip()
        basic = base64.b64encode(f"{user}:{token}".encode()).decode()
        return ["-c", f"http.extraHeader=Authorization: Basic {basic}"]

    @api.model
    def _sync_git_repo(self, url, cache_dir):
        """Clone or pull a single git repo; return local path or None on error."""
        local_name = self._repo_local_name(url)
        local_path = os.path.join(cache_dir, local_name)
        env = self._git_env()
        auth = self._git_auth_args(url)
        safe_url = self._safe_url(url)
        try:
            os.makedirs(cache_dir, exist_ok=True)
            if os.path.isdir(os.path.join(local_path, ".git")):
                result = subprocess.run(
                    ["git", "-C", local_path, *auth, "pull", "--ff-only", "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env=env,
                )
                if result.returncode != 0:
                    _logger.warning("Process library: git pull failed for %s: %s", safe_url, result.stderr)
            else:
                result = subprocess.run(
                    ["git", *auth, "clone", "--depth", "1", "--quiet", url, local_path],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env=env,
                )
                if result.returncode != 0:
                    _logger.warning("Process library: git clone failed for %s: %s", safe_url, result.stderr)
                    return None
        except subprocess.TimeoutExpired:
            _logger.warning("Process library: git operation timed out for %s", safe_url)
            return None
        except Exception as exc:
            _logger.warning("Process library: git error for %s: %s", safe_url, exc)
            return None
        return local_path if os.path.isdir(local_path) else None

    @api.model
    def sync_git_repos(self):
        """Clone/pull all configured git repos; return list of (label, local_path)."""
        icp = self.env["ir.config_parameter"].sudo()
        urls = [
            u.strip()
            for u in (icp.get_param("deltatech_business_process.process_library_git_repos") or "").split(",")
            if u.strip()
        ]
        cache_dir = self._git_repos_cache_dir()
        synced = []
        for url in urls:
            local_path = self._sync_git_repo(url, cache_dir)
            if local_path:
                label = self._repo_local_name(url)
                synced.append((label, local_path))
                _logger.info("Process library: synced git repo %s → %s", self._safe_url(url), local_path)
        return synced

    @api.model
    def _iter_process_sources(self):
        """Return ``[(label, base_dir), ...]`` for the eligible sources.

        Sources: (1) installed Odoo modules with a ``processes/`` sub-folder,
        (2) git repos configured via ``process_library_git_repos`` (root layout,
        no ``processes/`` sub-folder needed — process folders sit at repo root).
        """
        icp = self.env["ir.config_parameter"].sudo()
        whitelist = [
            m.strip()
            for m in (icp.get_param("deltatech_business_process.process_library_whitelist") or "").split(",")
            if m.strip()
        ]
        autodiscover = icp.get_param("deltatech_business_process.process_library_autodiscover", "1") == "1"

        sources = []
        seen = set()

        def _add(module_name):
            if module_name in seen:
                return
            base = self._module_processes_dir(module_name)
            if base:
                seen.add(module_name)
                sources.append((module_name, base))

        if whitelist:
            for module_name in whitelist:
                _add(module_name)
        elif autodiscover:
            installed = self.env["ir.module.module"].search([("state", "=", "installed")])
            for module_name in sorted(installed.mapped("name")):
                _add(module_name)

        # Git repos — cloned on demand; root of repo = processes base dir
        for label, local_path in self.sync_git_repos():
            if label not in seen:
                seen.add(label)
                sources.append((label, local_path))

        return sources

    @api.model
    def _read_folder(self, base, folder):
        path = os.path.join(base, folder, "process.json")
        if not os.path.isfile(path):
            return []
        try:
            with open(path, encoding="utf-8-sig") as fh:
                data = json.load(fh)
        except (ValueError, OSError) as exc:
            _logger.warning("Process library: cannot read %s: %s", path, exc)
            return []
        return data if isinstance(data, list) else [data]

    @api.model
    def available_processes(self):
        """List of dicts {source_module, folder, code, name, area, modules, has_screenshots}."""
        out = []
        for module_name, base in self._iter_process_sources():
            for folder in sorted(os.listdir(base)):
                items = self._read_folder(base, folder)
                if not items:
                    continue
                item = items[0]
                shots = os.path.join(base, folder, "screenshots")
                has_shots = os.path.isdir(shots) and any(f.endswith(".png") for f in os.listdir(shots))
                out.append(
                    {
                        "source_module": module_name,
                        "folder": folder,
                        "code": item.get("code") or "",
                        "name": item.get("name") or "",
                        "area": item.get("area") or "",
                        "modules": ", ".join(item.get("modules") or []),
                        "has_screenshots": has_shots,
                    }
                )
        return out

    @api.model
    def import_processes(self, refs, project=None, include_durations=True):
        """Import the processes identified by ``{module, folder}`` references.

        The reference is composite (module + folder) because folder names may
        collide across different sources. ``include_durations`` toggles whether
        the exported duration figures are imported onto each process.
        """
        created = self.env["business.process"]
        bases = dict(self._iter_process_sources())
        for ref in refs or []:
            module_name = (ref or {}).get("module")
            folder = (ref or {}).get("folder")
            base = bases.get(module_name)
            if not base or not folder:
                continue
            for item in self._read_folder(base, folder):
                proc = self._load_process(item, project, include_durations=include_durations)
                if proc:
                    self._attach_documents(base, folder, proc)
                    created |= proc
        return created

    @api.model
    def _attach_bytes(self, process, name, content, mimetype):
        """Create/update a binary attachment on the process (idempotent by name)."""
        if not content:
            return
        vals = {
            "name": name,
            "type": "binary",
            "datas": base64.b64encode(content),
            "res_model": "business.process",
            "res_id": process.id,
            "mimetype": mimetype,
        }
        existing = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "business.process"),
                ("res_id", "=", process.id),
                ("name", "=", name),
            ],
            limit=1,
        )
        if existing:
            existing.write(vals)
        else:
            self.env["ir.attachment"].create(vals)

    @api.model
    def _attach_fisa(self, process, base_name, html):
        """Attach the sheet as PDF (natively previewable in Odoo); fall back to HTML if PDF fails."""
        if not html:
            return
        from odoo.addons.deltatech_business_process.tools.html_to_pdf import html_to_pdf  # noqa: PLC0415

        pdf = html_to_pdf(html)
        if pdf:
            self._attach_bytes(process, f"{base_name}.pdf", pdf, "application/pdf")
        else:
            self._attach_bytes(process, f"{base_name}.html", html.encode("utf-8"), "text/html")

    @api.model
    def _attach_documents(self, base, folder, process):
        """Attach to business.process: the process sheet + the linked modules' sheets (PDF)."""
        # 1) the process sheet (from the source folder)
        fisa = os.path.join(base, folder, "fisa.html")
        if os.path.isfile(fisa):
            with open(fisa, encoding="utf-8") as fh:
                self._attach_fisa(process, f"Sheet_{process.code or folder}", fh.read())

        # 2) consultant sheets of the linked modules (FISA_CONSULTANT.md → PDF with screenshots)
        from odoo.addons.deltatech_business_process.tools.md_to_html import fisa_md_to_html  # noqa: PLC0415

        for module in process.module_ids:
            mpath = get_module_path(module.name)
            if not mpath:
                continue
            html = fisa_md_to_html(os.path.join(mpath, "readme", "FISA_CONSULTANT.md"))
            if html:
                self._attach_fisa(process, f"Sheet_module_{module.name}", html)

    @api.model
    def _get_or_create_area(self, name):
        if not name:
            return self.env["business.area"]
        area = self.env["business.area"].search([("name", "=", name)], limit=1)
        return area or self.env["business.area"].create({"name": name})

    @api.model
    def _get_or_create_process_group(self, name):
        if not name:
            return self.env["business.process.group"]
        group = self.env["business.process.group"].search([("name", "=", name)], limit=1)
        return group or self.env["business.process.group"].create({"name": name})

    @api.model
    def _get_or_create_implementation_stage(self, value):
        """Resolve an exported implementation stage to a stage record, creating it
        on the fly. Accepts the human-readable name and the legacy selection key
        (e.g. ``first_stage``), reusing the import wizard's legacy mapping."""
        if not value:
            return self.env["business.process.implementation.stage"]
        # noqa: PLC0415 — local import avoids a models→wizard dependency at load time
        from odoo.addons.deltatech_business_process.wizard.import_business_process import (  # noqa: PLC0415
            _LEGACY_STAGE_LABELS,
        )

        name = _LEGACY_STAGE_LABELS.get(value, value)
        stage_model = self.env["business.process.implementation.stage"]
        stage = stage_model.search([("name", "=", name)], limit=1)
        return stage or stage_model.create({"name": name})

    @api.model
    def _load_process(self, data, project=None, include_durations=True):
        code = data.get("code")
        domain = [("code", "=", code)]
        if project:
            domain.append(("project_id", "=", project.id))
        if code and self.env["business.process"].search(domain, limit=1):
            _logger.info("Process library: code %s already imported — skipped", code)
            return False  # already imported in this project

        vals = {
            "name": data.get("name"),
            "code": code,
            "area_id": self._get_or_create_area(data.get("area")).id,
            "description": data.get("description") or "",
            "process_group_id": self._get_or_create_process_group(data.get("process_group")).id,
            "module_type": data.get("module_type") or False,
            "implementation_stage_id": self._get_or_create_implementation_stage(data.get("implementation_stage")).id,
            "state": data.get("state") or "draft",
        }
        # Durations: imported only when the caller asks for it AND the export carried them.
        # ``duration_for_completion`` is a computed total — never written, it derives from these four.
        if include_durations and data.get("include_durations"):
            vals.update(
                {
                    "configuration_duration": data.get("configuration_duration") or 0.0,
                    "instructing_duration": data.get("instructing_duration") or 0.0,
                    "data_migration_duration": data.get("data_migration_duration") or 0.0,
                    "testing_duration": data.get("testing_duration") or 0.0,
                }
            )
        if project:
            vals["project_id"] = project.id
        process = self.env["business.process"].create(vals)

        for mod_name in data.get("modules") or []:
            module = self.env["ir.module.module"].search([("name", "=", mod_name)], limit=1)
            if module:
                process.module_ids = [(4, module.id)]

        for step in data.get("steps") or []:
            self.env["business.process.step"].create(
                {
                    "process_id": process.id,
                    "name": step.get("name"),
                    "sequence": step.get("sequence") or 10,
                    "description": step.get("description") or "",
                    "details": step.get("details") or "",
                }
            )

        raw_tests = data.get("tests") or []
        # JSON-urile mai vechi pot stoca un singur test ca dict, nu ca lista
        if isinstance(raw_tests, dict):
            raw_tests = [raw_tests]
        for test in raw_tests:
            test_rec = self.env["business.process.test"].create(
                {
                    "process_id": process.id,
                    "name": test.get("name"),
                    "scope": test.get("scope") or "user_acceptance",
                    "state": test.get("state") or "draft",
                }
            )
            for st in test.get("test_steps") or []:
                step = self.env["business.process.step"].search(
                    [("process_id", "=", process.id), ("name", "=", st.get("step"))], limit=1
                )
                if not step:
                    _logger.warning(
                        "Process library: step '%s' not found for test '%s' in process %s — skipped",
                        st.get("step"),
                        test.get("name"),
                        code,
                    )
                    continue
                self.env["business.process.step.test"].create(
                    {
                        "process_test_id": test_rec.id,
                        "step_id": step.id,
                        "process_id": process.id,
                        "result": st.get("result") or "draft",
                        "test_started": st.get("test_started") or False,
                    }
                )
        return process
