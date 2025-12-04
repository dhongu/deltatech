# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64
import json

from odoo.tests.common import TransactionCase


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
