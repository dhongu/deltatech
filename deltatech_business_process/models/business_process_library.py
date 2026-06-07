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
"""

import base64
import json
import logging
import os

from odoo import api, models
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
    def _iter_process_sources(self):
        """Return ``[(module_name, base_dir), ...]`` for the eligible sources.

        A source is an installed module that has a ``processes/`` folder. Order is
        deterministic (alphabetical by module name).
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
            return sources

        if autodiscover:
            installed = self.env["ir.module.module"].search([("state", "=", "installed")])
            for module_name in sorted(installed.mapped("name")):
                _add(module_name)
        return sources

    @api.model
    def _read_folder(self, base, folder):
        path = os.path.join(base, folder, "process.json")
        if not os.path.isfile(path):
            return []
        try:
            with open(path, encoding="utf-8") as fh:
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

        for test in data.get("tests") or []:
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
                self.env["business.process.step.test"].create(
                    {
                        "process_test_id": test_rec.id,
                        "step_id": step.id if step else False,
                        "process_id": process.id,
                        "result": st.get("result") or "draft",
                        "test_started": st.get("test_started") or False,
                    }
                )
        return process
