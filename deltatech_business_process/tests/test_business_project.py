# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestBusinessProject(TransactionCase):
    def setUp(self):
        super().setUp()
        # Minimal partner
        self.partner = self.env["res.partner"].search([], limit=1)
        if not self.partner:
            self.partner = self.env["res.partner"].create({"name": "Tester"})

        # Business area and group
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

        # Business project
        self.project = self.env["business.project"].create(
            {
                "name": "Implementation",
                "customer_id": self.partner.id,
                "project_type": "remote",
            }
        )

        # A process linked to the project
        self.process = self.env["business.process"].create(
            {
                "name": "Order to Cash",
                "area_id": self.area.id,
                "process_group_id": self.group.id,
                "project_id": self.project.id,
                "responsible_id": self.partner.id,
                "customer_id": self.partner.id,
            }
        )

    def test_action_methods_and_counters(self):
        # Initially, processes count should be 1
        self.project._compute_count_processes()
        self.assertEqual(self.project.count_processes, 1)

        # No issues/steps/developments yet
        self.project._compute_count_issues()
        self.project._compute_count_steps()
        self.project._compute_count_developments()
        self.assertEqual(self.project.count_issues, 0)
        self.assertEqual(self.project.count_steps, 0)
        self.assertEqual(self.project.count_developments, 0)

        # Step to increase step counter
        self.env["business.process.step"].create(
            {
                "name": "Validate Order",
                "process_id": self.process.id,
            }
        )
        self.project._compute_count_steps()
        self.assertEqual(self.project.count_steps, 1)

        # Create a development linked to the project to be found by action_view_developments
        dev_type = self.env["business.development.type"].create({"name": "Python"})
        self.env["business.development"].create(
            {
                "name": "Auto-confirm",
                "area_id": self.area.id,
                "type_id": dev_type.id,
                "project_id": self.project.id,
                "development_duration": 2.5,
                "approved": "approved",
            }
        )

        # Actions should return action dicts with domain/context
        act_proc = self.project.action_view_processes()
        self.assertIsInstance(act_proc, dict)
        self.assertIn("domain", act_proc)
        self.assertIn(("project_id", "=", self.project.id), act_proc["domain"])

        act_issue = self.project.action_view_issue()
        self.assertIsInstance(act_issue, dict)
        self.assertIn("domain", act_issue)
        self.assertIn(("project_id", "=", self.project.id), act_issue["domain"])

        act_step = self.project.action_view_step()
        self.assertIsInstance(act_step, dict)
        self.assertIn("domain", act_step)

        act_devs = self.project.action_view_developments()
        self.assertIsInstance(act_devs, dict)
        self.assertIn("domain", act_devs)

        # Calculate total duration aggregates processes + approved developments
        self.process.write(
            {
                "configuration_duration": 1.0,
                "instructing_duration": 1.0,
                "data_migration_duration": 1.0,
                "testing_duration": 1.0,
            }
        )
        self.process._compute_duration_for_completion()
        self.project.calculate_total_project_duration()
        # Process total 4.0 plus development 2.5
        self.assertAlmostEqual(self.project.total_project_duration, 6.5, places=2)

        # Attachment tree action
        act_att = self.project.attachment_tree_view()
        self.assertEqual(act_att.get("res_model"), "ir.attachment")
        self.assertEqual(act_att.get("type"), "ir.actions.act_window")

    def test_compute_attachment_ids_collects_related(self):
        Attachment = self.env["ir.attachment"].sudo()

        # Direct attachment on project
        att1 = Attachment.create(
            {
                "name": "proj.txt",
                "res_model": "business.project",
                "res_id": self.project.id,
                "datas": "Y29udGVudA==",  # base64 for 'content'
                "mimetype": "text/plain",
            }
        )

        # Attachment on a related process via chatter message
        # Create a message by posting on record; simplest way is to create an attachment linked to process
        att2 = Attachment.create(
            {
                "name": "proc.txt",
                "res_model": "business.process",
                "res_id": self.process.id,
                "datas": "Y29udGVudA==",
                "mimetype": "text/plain",
            }
        )

        # Also create a step and attach on it
        step = self.env["business.process.step"].create({"name": "Prepare", "process_id": self.process.id})
        att3 = Attachment.create(
            {
                "name": "step.txt",
                "res_model": step._name,
                "res_id": step.id,
                "datas": "Y29udGVudA==",
                "mimetype": "text/plain",
            }
        )

        # Trigger compute
        self.project._compute_attachment_ids()
        self.assertIn(att1, self.project.attachment_ids)
        self.assertIn(att2, self.project.attachment_ids)
        self.assertIn(att3, self.project.attachment_ids)

    def test_generate_excel_report_with_mocked_xlsxwriter(self):
        # Patch xlsxwriter used in the model to avoid external dependency
        fake_ws = MagicMock()

        class FakeWorkbook:
            def __init__(self, output, opts):
                self.output = output
                self.opts = opts

            def add_worksheet(self):
                return fake_ws

            def add_format(self, *_a, **_k):
                return object()

            def close(self):
                # Write something to buffer to simulate xlsx output
                self.output.write(b"ok")

        # Patch the xlsxwriter object in the same module as the BusinessProject model
        import importlib

        module_name = self.project.__class__.__module__
        bp = importlib.import_module(module_name)

        with patch.object(bp, "xlsxwriter", create=True) as xw:
            xw.Workbook.side_effect = lambda output, opts: FakeWorkbook(output, opts)
            # Ensure we have at least one process to iterate
            self.process.write(
                {
                    "configuration_duration": 0.0,
                    "instructing_duration": 0.0,
                    "data_migration_duration": 0.0,
                    "testing_duration": 0.0,
                }
            )
            content = self.project.generate_excel_report()
            self.assertIsInstance(content, (bytes, bytearray))
            self.assertTrue(len(content) > 0)

    def test_float_to_time(self):
        self.assertEqual(self.project.float_to_time(1.0), "01:00")
        self.assertEqual(self.project.float_to_time(0.08), "00:05")  # rounds to nearest 5 minutes
        self.assertEqual(self.project.float_to_time(2.25), "02:15")
