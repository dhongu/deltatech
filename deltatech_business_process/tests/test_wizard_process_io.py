# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64
import json

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.deltatech_business_process.wizard.import_business_process import _normalize_description


class TestBusinessProcessImportExport(TransactionCase):
    def setUp(self):
        super().setUp()
        # Minimal partner
        self.partner = self.env["res.partner"].search([], limit=1)
        if not self.partner:
            self.partner = self.env["res.partner"].create({"name": "Tester"})

        # Area and group
        self.area = self.env["business.area"].create(
            {
                "name": "ERP",
                "responsible_id": self.partner.id,
            }
        )
        self.group = self.env["business.process.group"].create(
            {
                "name": "Sales",
                "area_id": self.area.id,
            }
        )

        # Project and a process with one step and one test
        self.project = self.env["business.project"].create(
            {
                "name": "Implementation",
                "customer_id": self.partner.id,
                "project_type": "remote",
            }
        )
        self.process = self.env["business.process"].create(
            {
                "name": "Order to Cash",
                "code": "P-001",
                "area_id": self.area.id,
                "process_group_id": self.group.id,
                "project_id": self.project.id,
                "responsible_id": self.partner.id,
                "customer_id": self.partner.id,
            }
        )
        # Step
        self.step = self.env["business.process.step"].create(
            {"name": "Create SO", "code": "S-001", "process_id": self.process.id}
        )
        # Test + step test
        self.test = self.env["business.process.test"].create(
            {
                "name": "Internal Test",
                "process_id": self.process.id,
                "tester_id": self.partner.id,
                "scope": "internal",
                "state": "draft",
            }
        )
        self.step_test = self.env["business.process.step.test"].create(
            {
                "process_test_id": self.test.id,
                "step_id": self.step.id,
                "responsible_id": self.partner.id,
            }
        )

    def test_export_generates_json_with_selected_flags(self):
        # Create export wizard with flags
        wiz = (
            self.env["business.process.export"]
            .with_context(active_ids=self.process.ids, active_model="business.process")
            .create(
                {
                    "include_tests": True,
                    "include_responsible": True,
                    "include_customer_responsible": True,
                    "include_approved_by": True,
                    "include_support": True,
                    "include_durations": True,
                    "include_process_state": True,
                    "include_modules": False,
                }
            )
        )
        action = wiz.do_export()
        # Should return an action to open the wizard
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "business.process.export")
        # data_file should be set
        self.assertTrue(wiz.data_file)
        # Decode and parse JSON
        raw = base64.b64decode(wiz.data_file).decode("utf-8")
        data = json.loads(raw)
        # Accept both legacy dict payload and new list payload
        if isinstance(data, dict):
            processes = data.get("processes", [])
        else:
            processes = data
        self.assertTrue(isinstance(processes, list) and processes)
        rec = processes[0]
        # Basics present
        self.assertEqual(rec["name"], self.process.name)
        self.assertEqual(rec["code"], self.process.code)
        # Steps exported
        self.assertTrue(rec["steps"])  # contains our step
        # Tests exported because include_tests=True
        self.assertIn("tests", rec)
        self.assertTrue(rec["tests"])  # at least one test
        t0 = rec["tests"][0]
        self.assertIn("test_steps", t0)

    def test_import_creates_processes_steps_and_tests_in_new_project(self):
        # First export with tests
        export_wiz = (
            self.env["business.process.export"]
            .with_context(active_ids=self.process.ids, active_model="business.process")
            .create({"include_tests": True, "include_durations": True, "include_process_state": True})
        )
        export_wiz.do_export()
        self.assertTrue(export_wiz.data_file)

        # Create a fresh project to import into
        new_project = self.env["business.project"].create({"name": "Imported Project", "customer_id": self.partner.id})

        # Run import wizard using exported payload
        import_wiz = (
            self.env["business.process.import"]
            .with_context(active_ids=new_project.ids, active_model="business.project")
            .create({"name": "bp.json", "data_file": export_wiz.data_file})
        )
        action = import_wiz.do_import()
        self.assertIsInstance(action, dict)
        # Assert that process was created in the new project
        proc = self.env["business.process"].search(
            [("project_id", "=", new_project.id), ("code", "=", self.process.code)], limit=1
        )
        self.assertTrue(proc)
        # Steps imported
        steps = self.env["business.process.step"].search([("process_id", "=", proc.id)])
        self.assertTrue(steps)
        # Tests imported (since include_tests True)
        tests = self.env["business.process.test"].search([("process_id", "=", proc.id)])
        self.assertTrue(tests)

    def test_import_is_idempotent_updates_existing_records(self):
        # Export once
        export_wiz = (
            self.env["business.process.export"]
            .with_context(active_ids=self.process.ids, active_model="business.process")
            .create({"include_tests": True, "include_durations": True, "include_process_state": True})
        )
        export_wiz.do_export()
        payload = export_wiz.data_file

        # Import into project A
        import_wiz1 = (
            self.env["business.process.import"]
            .with_context(active_ids=self.project.ids, active_model="business.project")
            .create({"name": "bp.json", "data_file": payload})
        )
        import_wiz1.do_import()
        # Modify export JSON to change a description and re-import to ensure update path is taken
        raw = json.loads(base64.b64decode(payload).decode("utf-8"))
        # Handle both list and dict root formats
        if isinstance(raw, list):
            raw[0]["description"] = "Updated description"
        elif isinstance(raw, dict):
            if raw.get("processes"):
                raw["processes"][0]["description"] = "Updated description"
            else:
                # Fallback: ensure processes key exists
                raw["processes"] = []
        modified_payload = base64.b64encode(json.dumps(raw).encode("utf-8"))
        import_wiz2 = (
            self.env["business.process.import"]
            .with_context(active_ids=self.project.ids, active_model="business.project")
            .create({"name": "bp2.json", "data_file": modified_payload})
        )
        import_wiz2.do_import()
        # Ensure the existing process has been updated (not duplicated)
        procs = self.env["business.process"].search(
            [("project_id", "=", self.project.id), ("code", "=", self.process.code)]
        )
        self.assertEqual(len(procs), 1)

    def _export_payload_with_dev_and_issue(self):
        """Create a development + an issue on the project and export them along with the process."""
        dev_type = self.env["business.development.type"].create({"name": "Report"})
        self.development = self.env["business.development"].create(
            {
                "name": "Custom report",
                "code": "DEV-001",
                "area_id": self.area.id,
                "type_id": dev_type.id,
                "project_id": self.project.id,
                "note": "Some note",
            }
        )
        # Link the development to the exported step
        self.step.development_ids = [(4, self.development.id)]
        self.issue = self.env["business.issue"].create(
            {
                "name": "Wrong total",
                "code": "ISS-001",
                "project_id": self.project.id,
                "process_id": self.process.id,
                "area_id": self.area.id,
                "category": "defect",
                "severity": "major",
            }
        )
        export_wiz = (
            self.env["business.process.export"]
            .with_context(active_ids=self.process.ids, active_model="business.process")
            .create(
                {
                    "include_tests": True,
                    "include_durations": True,
                    "include_process_state": True,
                    "include_developments": True,
                    "include_issues": True,
                }
            )
        )
        export_wiz.do_export()
        return export_wiz.data_file

    def test_export_import_developments_and_issues(self):
        payload = self._export_payload_with_dev_and_issue()
        data = json.loads(base64.b64decode(payload).decode("utf-8"))
        self.assertTrue(data["developments"])
        self.assertTrue(data["issues"])
        # step exports the linked development reference
        self.assertIn("DEV-001", data["processes"][0]["steps"][0]["development_ids"])

        new_project = self.env["business.project"].create({"name": "Imported DI", "customer_id": self.partner.id})
        import_wiz = (
            self.env["business.process.import"]
            .with_context(active_ids=new_project.ids, active_model="business.project")
            .create({"name": "bp.json", "data_file": payload})
        )
        import_wiz.do_import()

        dev = self.env["business.development"].search([("project_id", "=", new_project.id), ("code", "=", "DEV-001")])
        self.assertEqual(len(dev), 1)
        self.assertIn("Some note", dev.note)  # html field
        issue = self.env["business.issue"].search([("project_id", "=", new_project.id), ("code", "=", "ISS-001")])
        self.assertEqual(len(issue), 1)
        self.assertEqual(issue.severity, "major")
        # the issue is relinked to the imported process by name
        self.assertEqual(issue.process_id.project_id, new_project)
        # the imported step is linked to the imported development
        step = self.env["business.process.step"].search(
            [("process_id.project_id", "=", new_project.id), ("code", "=", self.step.code)]
        )
        self.assertIn(dev, step.development_ids)

        # second import updates instead of duplicating
        import_wiz2 = (
            self.env["business.process.import"]
            .with_context(active_ids=new_project.ids, active_model="business.project")
            .create({"name": "bp.json", "data_file": payload})
        )
        import_wiz2.do_import()
        self.assertEqual(
            self.env["business.development"].search_count(
                [("project_id", "=", new_project.id), ("code", "=", "DEV-001")]
            ),
            1,
        )
        self.assertEqual(
            self.env["business.issue"].search_count([("project_id", "=", new_project.id), ("code", "=", "ISS-001")]),
            1,
        )

    def test_import_creates_missing_masterdata(self):
        # link an installed module so include_modules has content
        base_module = self.env["ir.module.module"].search([("name", "=", "base")], limit=1)
        self.process.module_ids = [(4, base_module.id)]
        payload = self._export_payload_with_dev_and_issue()
        data = json.loads(base64.b64decode(payload).decode("utf-8"))
        proc = data["processes"][0]
        # rewire every master-data reference to names that do not exist yet
        proc["responsible"] = "New Responsible"
        proc["customer"] = "New Customer"
        proc["approved"] = "New Approver"
        proc["support"] = "New Support"
        proc["area"] = "New Area"
        proc["process_group"] = "New Group"
        proc["include_modules"] = True
        proc["modules"] = ["base"]
        proc["steps"][0]["area"] = "New Step Area"
        proc["steps"][0]["transaction"] = "New Transaction"
        proc["tests"][0]["tester"] = "New Tester"
        data["developments"][0]["area"] = "New Dev Area"
        data["developments"][0]["type"] = "New Dev Type"
        data["issues"][0]["area"] = "New Issue Area"
        payload = base64.b64encode(json.dumps(data, default=str).encode("utf-8"))

        new_project = self.env["business.project"].create({"name": "Masterdata", "customer_id": self.partner.id})
        import_wiz = (
            self.env["business.process.import"]
            .with_context(active_ids=new_project.ids, active_model="business.project")
            .create({"name": "bp.json", "data_file": payload})
        )
        import_wiz.do_import()

        proc_rec = self.env["business.process"].search([("project_id", "=", new_project.id)], limit=1)
        self.assertEqual(proc_rec.responsible_id.name, "New Responsible")
        self.assertEqual(proc_rec.customer_id.name, "New Customer")
        self.assertEqual(proc_rec.approved_id.name, "New Approver")
        self.assertEqual(proc_rec.support_id.name, "New Support")
        self.assertEqual(proc_rec.area_id.name, "New Area")
        self.assertEqual(proc_rec.process_group_id.name, "New Group")
        self.assertIn(base_module, proc_rec.module_ids)
        step = proc_rec.step_ids[0]
        # the step area is a stored related field of the process area
        self.assertEqual(step.area_id.name, "New Area")
        self.assertEqual(step.transaction_id.name, "New Transaction")
        test = self.env["business.process.test"].search([("process_id", "=", proc_rec.id)], limit=1)
        self.assertEqual(test.tester_id.name, "New Tester")
        dev = self.env["business.development"].search([("project_id", "=", new_project.id)], limit=1)
        self.assertEqual(dev.area_id.name, "New Dev Area")
        self.assertEqual(dev.type_id.name, "New Dev Type")
        issue = self.env["business.issue"].search([("project_id", "=", new_project.id)], limit=1)
        self.assertEqual(issue.area_id.name, "New Issue Area")

    def test_import_from_process_context(self):
        payload = self._export_payload_with_dev_and_issue()
        import_wiz = (
            self.env["business.process.import"]
            .with_context(active_ids=self.process.ids, active_model="business.process")
            .create({"name": "bp.json", "data_file": payload})
        )
        import_wiz.do_import()
        # project resolved from the process; the process was updated in place
        self.assertEqual(
            self.env["business.process"].search_count(
                [("project_id", "=", self.project.id), ("code", "=", self.process.code)]
            ),
            1,
        )

    def test_import_without_project_raises(self):
        import_wiz = (
            self.env["business.process.import"]
            .with_context(active_ids=[], active_model="business.project")
            .create({"name": "bp.json", "data_file": base64.b64encode(b"{}")})
        )
        with self.assertRaises(UserError):
            import_wiz.do_import()

    def test_do_back_wizards(self):
        export_wiz = self.env["business.process.export"].create({})
        action = export_wiz.do_back()
        self.assertEqual(export_wiz.state, "choose")
        self.assertEqual(action.get("res_model"), "business.process.export")

        import_wiz = self.env["business.process.import"].create({})
        action = import_wiz.do_back()
        self.assertEqual(import_wiz.state, "get")
        self.assertEqual(action.get("res_model"), "business.process.import")

    def test_normalize_description(self):
        self.assertEqual(_normalize_description(False), "")
        self.assertEqual(_normalize_description(""), "")
        self.assertEqual(_normalize_description("<p>Hello &amp; bye</p>"), "Hello & bye")
        self.assertEqual(_normalize_description(42), "42")


class TestLibraryImportLine(TransactionCase):
    def setUp(self):
        super().setUp()
        # partner creation can hit DB-specific constraints, reuse an existing one
        self.partner = self.env["res.partner"].search([], limit=1)
        if not self.partner:
            self.partner = self.env["res.partner"].create({"name": "Customer"})
        self.project = self.env["business.project"].create({"name": "Library Project", "customer_id": self.partner.id})
        self.area = self.env["business.area"].create({"name": "Library Area"})
        self.process = self.env["business.process"].create(
            {"name": "Proc", "code": "P-LIB", "project_id": self.project.id, "area_id": self.area.id}
        )
        self.Line = self.env["business.process.library.import.line"]

    def test_resolve_project_from_context(self):
        project = self.Line.with_context(
            active_ids=self.project.ids, active_model="business.project"
        )._resolve_project_from_context()
        self.assertEqual(project, self.project)

        project = self.Line.with_context(
            active_ids=self.process.ids, active_model="business.process"
        )._resolve_project_from_context()
        self.assertEqual(project, self.project)

        with self.assertRaises(UserError):
            self.Line.with_context(active_ids=[], active_model="business.project")._resolve_project_from_context()

    def test_action_open_library(self):
        action = self.Line.with_context(
            active_ids=self.project.ids, active_model="business.project"
        ).action_open_library()
        self.assertEqual(action.get("type"), "ir.actions.act_window")
        self.assertEqual(action.get("res_model"), self.Line._name)
        # the action domain points at the (re)created lines of this project
        lines = self.Line.search([("project_id", "=", self.project.id)])
        self.assertEqual(set(action["domain"][0][2]), set(lines.ids))

    def test_populate_lines_is_idempotent(self):
        lines1 = self.Line._populate_lines(self.project)
        lines2 = self.Line._populate_lines(self.project)
        # previous lines are removed on re-population
        self.assertFalse(lines1.exists() - lines2.exists())
        self.assertEqual(len(self.Line.search([("project_id", "=", self.project.id)])), len(lines2))

    def test_action_import_selected_empty_raises(self):
        with self.assertRaises(UserError):
            self.Line.action_import_selected()
        # a line without folder is filtered out as well
        line = self.Line.create({"project_id": self.project.id, "name": "x", "code": "c", "folder": False})
        with self.assertRaises(UserError):
            line.action_import_selected()
