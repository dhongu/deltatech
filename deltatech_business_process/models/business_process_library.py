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
    def _sync_git_repo(self, url, cache_dir):
        """Clone or pull a single git repo; return local path or None on error."""
        local_name = self._repo_local_name(url)
        local_path = os.path.join(cache_dir, local_name)
        try:
            os.makedirs(cache_dir, exist_ok=True)
            if os.path.isdir(os.path.join(local_path, ".git")):
                result = subprocess.run(
                    ["git", "-C", local_path, "pull", "--ff-only", "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode != 0:
                    _logger.warning("Process library: git pull failed for %s: %s", url, result.stderr)
            else:
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", "--quiet", url, local_path],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    _logger.warning("Process library: git clone failed for %s: %s", url, result.stderr)
                    return None
        except subprocess.TimeoutExpired:
            _logger.warning("Process library: git operation timed out for %s", url)
            return None
        except Exception as exc:
            _logger.warning("Process library: git error for %s: %s", url, exc)
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
                _logger.info("Process library: synced git repo %s → %s", url, local_path)
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
    def import_processes(self, refs, project=None):
        """Import the processes identified by ``{module, folder}`` references.

        The reference is composite (module + folder) because folder names may
        collide across different sources.
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
                proc = self._load_process(item, project)
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
    def _load_process(self, data, project=None):
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
        }
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
