# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Regression tests for the source-audit issues #3368-#3376 (BUSINESS-004..014)."""

import base64
import json
from unittest.mock import patch

from lxml import etree

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval

PARAM_AUTODISCOVER = "deltatech_business_process.process_library_autodiscover"


@tagged("post_install", "-at_install")
class TestAuditFixes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env["res.partner"].create({"name": "Audit PM", "email": "audit.pm@example.com"})
        cls.project = cls.env["business.project"].create(
            {"name": "Audit project", "project_manager_id": cls.manager.id}
        )
        cls.project_no_pm = cls.env["business.project"].create({"name": "Audit project without PM"})
        cls.area = cls.env["business.area"].create({"name": "Audit area"})
        cls.dev_type = cls.env["business.development.type"].create({"name": "Audit type"})

    def _development(self, name, project):
        return self.env["business.development"].create(
            {"name": name, "area_id": self.area.id, "type_id": self.dev_type.id, "project_id": project.id}
        )

    # BUSINESS-004 (#3368)
    def test_batch_development_approval(self):
        dev1 = self._development("Dev 1", self.project)
        dev2 = self._development("Dev 2", self.project)
        dev3 = self._development("Dev 3", self.project_no_pm)
        (dev1 | dev2 | dev3).write({"approved": "approved"})
        for dev in dev1 | dev2:
            self.assertTrue(dev.message_ids.filtered(lambda m: "Date of approval" in str(m.body)))
            mails = self.env["mail.mail"].search([("model", "=", "business.development"), ("res_id", "=", dev.id)])
            self.assertEqual(len(mails), 1)
        self.assertFalse(dev3.message_ids.filtered(lambda m: "Date of approval" in str(m.body)))

    # BUSINESS-006 (#3370)
    def _process_payload(self, process, durations):
        wiz = (
            self.env["business.process.export"]
            .with_context(active_ids=process.ids, active_model="business.process")
            .create({"include_durations": True, "include_process_state": True})
        )
        wiz.do_export()
        data = json.loads(base64.b64decode(wiz.data_file).decode("utf-8"))
        processes = data["processes"] if isinstance(data, dict) else data
        processes[0].update(durations)
        if not durations.get("include_durations", True):
            processes[0]["include_durations"] = False
        return base64.b64encode(json.dumps(data).encode("utf-8"))

    def _import(self, payload):
        self.env["business.process.import"].with_context(
            active_ids=self.project.ids, active_model="business.project"
        ).create({"name": "bp.json", "data_file": payload}).do_import()

    def test_reimport_updates_durations(self):
        process = self.env["business.process"].create(
            {
                "name": "Audit process",
                "code": "AUDIT-006",
                "area_id": self.area.id,
                "project_id": self.project.id,
                "configuration_duration": 1.0,
                "instructing_duration": 1.0,
                "data_migration_duration": 1.0,
                "testing_duration": 1.0,
            }
        )
        new = {
            "configuration_duration": 2.0,
            "instructing_duration": 3.0,
            "data_migration_duration": 4.0,
            "testing_duration": 5.0,
            "duration_for_completion": 14.0,
        }
        self._import(self._process_payload(process, new))
        self.assertRecordValues(
            process,
            [
                {
                    "configuration_duration": 2.0,
                    "instructing_duration": 3.0,
                    "data_migration_duration": 4.0,
                    "testing_duration": 5.0,
                    "duration_for_completion": 14.0,
                }
            ],
        )
        # without durations in the file, the existing ones are kept
        payload = self._process_payload(process, dict(new, configuration_duration=9.0, include_durations=False))
        self._import(payload)
        self.assertEqual(process.configuration_duration, 2.0)
        self.assertEqual(process.duration_for_completion, 14.0)

    # BUSINESS-007 (#3371)
    def test_autodiscover_setting_roundtrip(self):
        library = self.env["business.process.library"]
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("deltatech_business_process.process_library_whitelist", False)

        def fake_dir(lib, module_name):
            return "/tmp" if module_name == "base" else None

        with (
            patch.object(type(library), "_module_processes_dir", fake_dir),
            patch.object(type(library), "sync_git_repos", lambda lib: []),
        ):
            self.env["res.config.settings"].create({"process_library_autodiscover": True}).execute()
            self.assertTrue(self.env["res.config.settings"].create({}).process_library_autodiscover)
            self.assertIn("base", dict(library._iter_process_sources()))

            self.env["res.config.settings"].create({"process_library_autodiscover": False}).execute()
            self.assertFalse(self.env["res.config.settings"].create({}).process_library_autodiscover)
            self.assertNotIn("base", dict(library._iter_process_sources()))

            # legacy values written by older versions keep working
            icp.set_param(PARAM_AUTODISCOVER, "True")
            self.assertIn("base", dict(library._iter_process_sources()))
            icp.set_param(PARAM_AUTODISCOVER, "1")
            self.assertIn("base", dict(library._iter_process_sources()))

    # BUSINESS-008 (#3372)
    def test_rejected_filter(self):
        rejected = self._development("Rejected dev", self.project)
        rejected.write({"approved": "rejected", "state": "specification"})
        approved = self._development("Approved dev", self.project)
        approved.write({"approved": "approved"})
        arch = self.env["business.development"].get_views([(False, "search")])["views"]["search"]["arch"]
        node = etree.fromstring(arch).xpath("//filter[@name='is_rejected']")[0]
        domain = safe_eval(node.get("domain"))
        found = self.env["business.development"].search(domain + [("project_id", "=", self.project.id)])
        self.assertEqual(found, rejected)

    # BUSINESS-013 (#3375)
    def test_open_issue_gets_code(self):
        open_issue = self.env["business.open.issue"].create({"name": "Audit open issue", "project_id": self.project.id})
        issue = self.env["business.issue"].create({"name": "Audit issue", "project_id": self.project.id})
        self.assertTrue(open_issue.code)
        self.assertTrue(open_issue.code.startswith("OI"))
        self.assertNotEqual(open_issue.code, issue.code)

    # BUSINESS-010 (#3373)
    def test_abandon_checks(self):
        process = self.env["business.process"].create(
            {"name": "Audit abandon", "area_id": self.area.id, "project_id": self.project.id}
        )
        bp_admin = new_test_user(
            self.env,
            login="audit_bp_admin",
            groups="base.group_user,deltatech_business_process.group_business_process_manager",
        )
        with self.assertRaises(AccessError):
            process.with_user(bp_admin).button_abandon()
        self.assertEqual(process.state, "draft")

        process.state = "production"
        with self.assertRaises(UserError):
            process.button_abandon()
        self.assertEqual(process.state, "production")

        process.state = "test"
        process.button_abandon()
        self.assertEqual(process.state, "abandoned")
        with self.assertRaises(UserError):
            process.button_abandon()

    # BUSINESS-014 (#3376)
    def test_open_issue_template_translated(self):
        self.env["res.lang"]._activate_lang("ro_RO")
        self.env["ir.module.module"]._load_module_terms(["deltatech_business_process"], ["ro_RO"], overwrite=True)
        template = self.env.ref("deltatech_business_process.email_template_open_issue_submitted")
        template_ro = template.with_context(lang="ro_RO")
        self.assertNotEqual(template_ro.subject, "Open Issue Submitted")
        self.assertNotIn("Please check and inform colleagues", str(template_ro.body_html))
