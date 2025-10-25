# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestBusinessIssue(TransactionCase):
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

        # Project and process with one step
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
        self.step = self.env["business.process.step"].create({"name": "Create SO", "process_id": self.process.id})

        # A Business Process Test and a Step Test
        self.bpt = self.env["business.process.test"].create(
            {
                "name": "",
                "process_id": self.process.id,
                "scope": "internal",
                "tester_id": self.partner.id,
            }
        )
        self.step_test = self.env["business.process.step.test"].create(
            {
                "process_test_id": self.bpt.id,
                "step_id": self.step.id,
                "responsible_id": self.partner.id,
            }
        )

    def _patch_send_issue_mail(self):
        # Helper context manager to patch send_issue_mail in create flows
        import importlib

        module = importlib.import_module("odoo.addons.deltatech_business_process.models.business_issue")
        return patch.object(module.BusinessIssue, "send_issue_mail", autospec=True)

    def test_create_assigns_code_without_sending_mail(self):
        with self._patch_send_issue_mail() as mocked:
            issue = self.env["business.issue"].create(
                {
                    "name": "Issue A",
                    "project_id": self.project.id,
                }
            )
            # send_issue_mail should be called but patched to avoid external template
            self.assertTrue(mocked.called)
            self.assertTrue(issue.code, "A sequence code should be assigned on create")

    def test_onchange_process_id_sets_related_fields(self):
        issue = self.env["business.issue"].new(
            {
                "name": "Issue B",
                "project_id": self.project.id,
                "process_id": self.process.id,
            }
        )
        issue._onchange_process_id()
        self.assertEqual(issue.project_id, self.project)
        self.assertEqual(issue.customer_id, self.process.customer_id)
        self.assertEqual(issue.responsible_id, self.process.responsible_id)
        self.assertEqual(issue.area_id, self.process.area_id)

    def test_onchange_step_test_id_sets_fields_and_validates(self):
        issue = self.env["business.issue"].new(
            {
                "name": "Issue C",
                "project_id": self.project.id,
                "step_test_id": self.step_test.id,
            }
        )
        issue._onchange_step_test_id()
        self.assertEqual(issue.process_id, self.process)
        self.assertEqual(issue.raise_by_id, self.bpt.tester_id)

        # Mark test done and ensure onchange raises
        self.bpt.action_done()
        issue2 = self.env["business.issue"].new(
            {
                "name": "Issue D",
                "project_id": self.project.id,
                "step_test_id": self.step_test.id,
            }
        )
        with self.assertRaises(UserError):
            issue2._onchange_step_test_id()

    def test_button_send_marks_failed_and_open(self):
        with self._patch_send_issue_mail():
            issue = self.env["business.issue"].create(
                {
                    "name": "Issue E",
                    "project_id": self.project.id,
                    "step_test_id": self.step_test.id,
                    "raise_by_id": self.partner.id,
                    "responsible_id": self.partner.id,
                    "customer_id": self.partner.id,
                }
            )
        issue.button_send()
        self.assertEqual(issue.state, "open")
        self.assertEqual(self.step_test.result, "failed")
        # Followers should include participants (can be empty in minimal DB, but method is idempotent)
        self.assertIn(self.partner, issue.message_partner_ids)

    def test_button_solved_requires_fields_then_sets_state(self):
        with self._patch_send_issue_mail():
            issue = self.env["business.issue"].create(
                {
                    "name": "Issue F",
                    "project_id": self.project.id,
                }
            )
        # Missing required solution fields
        with self.assertRaises(UserError):
            issue.button_solved()
        # Provide solution details
        issue.solution = "Fixed by patch"
        issue.solution_date = issue.open_date
        issue.button_solved()
        self.assertEqual(issue.state, "solved")

    def test_transitions_in_progress_in_test_reopened_draft(self):
        with self._patch_send_issue_mail():
            issue = self.env["business.issue"].create(
                {
                    "name": "Issue G",
                    "project_id": self.project.id,
                }
            )
        issue.button_in_progress()
        self.assertEqual(issue.state, "allocated")
        issue.button_in_test()
        self.assertEqual(issue.state, "in_test")
        issue.button_reopened()
        self.assertEqual(issue.state, "reopened")
        issue.button_draft()
        self.assertEqual(issue.state, "draft")

    def test_button_done_validations_and_step_pass_logic(self):
        # Case 1: cannot close without closed_date
        with self._patch_send_issue_mail():
            issue1 = self.env["business.issue"].create(
                {
                    "name": "Issue H1",
                    "project_id": self.project.id,
                    "step_test_id": self.step_test.id,
                }
            )
        with self.assertRaises(UserError):
            issue1.button_done()

        # Set closed_date; closed_by_id should auto-fill if missing
        issue1.closed_date = issue1.open_date
        issue1.button_done()
        self.assertEqual(issue1.state, "closed")
        self.assertTrue(issue1.closed_by_id)
        # Since it's the only issue for the step_test now, result should be passed
        self.assertEqual(self.step_test.result, "passed")

        # Case 2: When another issue on same step_test is still open, do not mark passed
        # Recreate fresh step test to isolate
        step_test2 = self.env["business.process.step.test"].create(
            {
                "process_test_id": self.bpt.id,
                "step_id": self.step.id,
            }
        )
        with self._patch_send_issue_mail():
            self.env["business.issue"].create(
                {
                    "name": "Issue I-open",
                    "project_id": self.project.id,
                    "step_test_id": step_test2.id,
                }
            )
            to_close = self.env["business.issue"].create(
                {
                    "name": "Issue I-close",
                    "project_id": self.project.id,
                    "step_test_id": step_test2.id,
                }
            )
        # Leave open_issue in non-closed state
        to_close.closed_date = to_close.open_date
        to_close.button_done()
        self.assertEqual(to_close.state, "closed")
        # Should not set step test to passed because another issue is still open
        self.assertNotEqual(step_test2.result, "passed")
