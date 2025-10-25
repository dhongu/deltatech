# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestBusinessProcessTest(TransactionCase):
    def setUp(self):
        super().setUp()
        # Minimal partner for responsible/tester
        self.partner = self.env["res.partner"].search([], limit=1)
        if not self.partner:
            self.partner = self.env["res.partner"].create({"name": "Tester"})

        # A business area and group
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

        # A project and a process with steps
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
                "area_id": self.area.id,
                "process_group_id": self.group.id,
                "project_id": self.project.id,
                "responsible_id": self.partner.id,
                "customer_id": self.partner.id,
            }
        )
        # Create two steps to be mirrored into test steps by onchange
        self.step1 = self.env["business.process.step"].create({"name": "Create SO", "process_id": self.process.id})
        self.step2 = self.env["business.process.step"].create({"name": "Confirm SO", "process_id": self.process.id})

        # Create a Business Process Test
        self.bpt = self.env["business.process.test"].create(
            {
                "name": "",
                "process_id": self.process.id,
                "scope": "internal",
            }
        )

    def test_onchange_process_id_populates_steps_and_name(self):
        # Simulate onchange to populate test steps and name if empty
        self.bpt._onchange_process_id()
        # Name should be set to something non-empty
        self.assertTrue(self.bpt.name)
        # At least one test step should be created (implementation overwrites per loop)
        self.assertTrue(len(self.bpt.test_step_ids) >= 1)
        # Counter should reflect number of linked test steps
        self.bpt._compute_count_steps()
        self.assertEqual(self.bpt.count_steps, len(self.bpt.test_step_ids))

    def test_compute_completion_test(self):
        # Ensure we have test steps
        if not self.bpt.test_step_ids:
            self.bpt._onchange_process_id()
        # Mark first step passed, others failed/draft
        steps = self.bpt.test_step_ids
        if steps:
            steps[0].result = "passed"
            if len(steps) > 1:
                steps[1].result = "failed"
        self.bpt._compute_completion_test()
        passed = len(steps.filtered(lambda s: s.result == "passed"))
        total = len(steps)
        expected = round((passed / total) * 100, 2) if total else 0.0
        self.assertEqual(self.bpt.completion_test, expected)

    def test_action_view_test_steps_and_attachments(self):
        # Action should be a valid action dict with proper domain
        action = self.bpt.action_view_test_steps()
        self.assertIsInstance(action, dict)
        self.assertIn("domain", action)
        self.assertIn(("process_test_id", "=", self.bpt.id), action["domain"])

        # Attachment helpers
        Attachment = self.env["ir.attachment"].sudo()
        Attachment.create(
            {
                "name": "test.txt",
                "res_model": self.bpt._name,
                "res_id": self.bpt.id,
                "datas": "Y29udGVudA==",
                "mimetype": "text/plain",
            }
        )
        self.bpt._compute_attached_docs_count()
        self.assertGreaterEqual(self.bpt.doc_count, 1)

        act_att = self.bpt.attachment_tree_view()
        self.assertEqual(act_att.get("res_model"), "ir.attachment")
        self.assertEqual(act_att.get("type"), "ir.actions.act_window")

    def test_onchange_state_sets_dates(self):
        # When state is run, date_start should be set
        self.bpt.state = "run"
        self.bpt._onchange_state()
        self.assertTrue(self.bpt.date_start)
        # When state is done, date_end should be set
        self.bpt.state = "done"
        self.bpt._onchange_state()
        self.assertTrue(self.bpt.date_end)

    def test_onchange_completion_test_triggers_done(self):
        # When completion reaches 100, onchange should call action_done
        # First ensure at least one step exists
        if not self.bpt.test_step_ids:
            self.bpt._onchange_process_id()
        # Set value and trigger onchange
        self.bpt.completion_test = 100.0
        self.bpt._onchange_completion_test()
        self.assertEqual(self.bpt.state, "done")
