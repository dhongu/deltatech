# © 2026 Deltatech
# See README.rst file on addons root folder for license details

import importlib
from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase


class TestWorkflowFixes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area_responsible = cls.env["res.partner"].create({"name": "Area Responsible"})
        cls.consultant = cls.env["res.partner"].create({"name": "Consultant"})
        cls.area = cls.env["business.area"].create({"name": "Sales", "responsible_id": cls.area_responsible.id})
        cls.project = cls.env["business.project"].create({"name": "Implementation", "project_type": "remote"})
        cls.process = cls._create_process("Order to Cash", cls.consultant)
        cls.process2 = cls._create_process("Return", cls.area_responsible)

        cls.responsible_user = new_test_user(
            cls.env,
            login="bp_responsible",
            groups="base.group_user,deltatech_business_process.group_business_process_responsible",
        )
        cls.end_user = new_test_user(
            cls.env,
            login="bp_end_user",
            groups="base.group_user,deltatech_business_process.group_business_end_user",
        )

    @classmethod
    def _create_process(cls, name, responsible):
        process = cls.env["business.process"].create(
            {
                "name": name,
                "area_id": cls.area.id,
                "project_id": cls.project.id,
                "responsible_id": responsible.id,
            }
        )
        cls.env["business.process.step"].create({"name": f"{name} step 1", "process_id": process.id})
        cls.env["business.process.step"].create({"name": f"{name} step 2", "process_id": process.id})
        return process

    def _run_test(self, process, scope):
        test = process._start_test(scope)
        test.action_run()
        return test

    # 1. raport Excel: coloanele Testare / Migrare date
    def test_excel_report_columns_match_headers(self):
        self.project.process_ids.write(
            {
                "configuration_duration": 0.0,
                "instructing_duration": 0.0,
                "data_migration_duration": 0.0,
                "testing_duration": 0.0,
            }
        )
        self.process.write(
            {
                "configuration_duration": 1.0,
                "instructing_duration": 2.0,
                "testing_duration": 3.0,
                "data_migration_duration": 4.0,
            }
        )
        fake_ws = MagicMock()
        workbook = MagicMock()
        workbook.add_worksheet.return_value = fake_ws
        module = importlib.import_module("odoo.addons.deltatech_business_process.models.business_project")
        with patch.object(module, "xlsxwriter") as xw:
            xw.Workbook.return_value = workbook
            self.project.generate_excel_report()

        cells = {(c.args[0], c.args[1]): c.args[2] for c in fake_ws.write.call_args_list}
        self.assertEqual(cells[(0, 4)], "Testing duration")
        self.assertEqual(cells[(0, 5)], "Data Migration Duration")
        process_row = next(row for (row, col), value in cells.items() if col == 1 and value == self.process.name)
        self.assertEqual(cells[(process_row, 4)], "03:00")
        self.assertEqual(cells[(process_row, 5)], "04:00")
        total_row = next(row for (row, col), value in cells.items() if col == 1 and value == "Total")
        self.assertEqual(cells[(total_row, 4)], "03:00")
        self.assertEqual(cells[(total_row, 5)], "04:00")

    # 2. responsabilul de proces: creare în zonă cu responsabil + tranziții de stare
    def test_responsible_creates_process_in_area_with_responsible(self):
        process = (
            self.env["business.process"]
            .with_user(self.responsible_user)
            .create({"name": "New process", "area_id": self.area.id, "project_id": self.project.id})
        )
        self.assertEqual(process.responsible_id, self.area_responsible)

    def test_responsible_can_change_process_state(self):
        process = self.process.with_user(self.responsible_user)
        process.button_start_design()
        self.assertEqual(self.process.state, "design")
        process.button_start_test()
        self.assertEqual(self.process.state, "test")
        process.button_end_test()
        self.assertEqual(self.process.state, "ready")
        process.button_go_live()
        self.assertEqual(self.process.state, "production")
        process.button_draft()
        self.assertEqual(self.process.state, "draft")

    def test_end_user_cannot_change_process_state(self):
        with self.assertRaises(AccessError):
            self.process.with_user(self.end_user).button_start_design()
        self.assertEqual(self.process.state, "draft")

    # 3. pornirea testelor pe mai multe procese
    def test_start_test_multi_record(self):
        processes = self.process | self.process2
        tests = processes._start_test("internal")
        self.assertEqual(len(tests), 2)
        self.assertEqual(tests.process_id, processes)
        for test in tests:
            self.assertEqual(test.tester_id, test.process_id.responsible_id)
            self.assertEqual(len(test.test_step_ids), 2)

    # 4. butonul inteligent „Start Test" nu mai creează un test la fiecare click
    def test_action_view_acceptance_tests_reuses_existing(self):
        action = self.process.action_view_acceptance_tests()
        uat = self.process.test_ids.filtered(lambda t: t.scope == "user_acceptance")
        self.assertEqual(len(uat), 1)
        self.assertEqual(action["res_id"], uat.id)

        action = self.process.action_view_acceptance_tests()
        self.assertEqual(len(self.process.test_ids.filtered(lambda t: t.scope == "user_acceptance")), 1)
        self.assertEqual(action["res_id"], uat.id)

    def test_action_view_acceptance_tests_several_opens_list(self):
        self.process._start_test("user_acceptance")
        self.process._start_test("user_acceptance")
        action = self.process.action_view_acceptance_tests()
        self.assertEqual(len(self.process.test_ids.filtered(lambda t: t.scope == "user_acceptance")), 2)
        self.assertFalse(action.get("res_id"))
        self.assertIn(("scope", "=", "user_acceptance"), action["domain"])

    # 5. finalizarea testului
    def test_action_done_keeps_failed_steps(self):
        test = self._run_test(self.process, "internal")
        failed, untouched = test.test_step_ids
        failed.result = "failed"
        test.action_done()
        self.assertEqual(failed.result, "failed")
        self.assertEqual(untouched.result, "passed")

    def test_action_done_keeps_date_start(self):
        test = self._run_test(self.process, "internal")
        start = fields.Date.today() - timedelta(days=10)
        test.date_start = start
        test.action_done()
        self.assertEqual(test.date_start, start)
        self.assertEqual(test.date_end, fields.Date.today())

    def test_action_done_does_not_downgrade_production(self):
        self.process.state = "production"
        test = self._run_test(self.process, "user_acceptance")
        test.action_done()
        self.assertEqual(self.process.state, "production")

    def test_action_done_moves_tested_process_to_ready(self):
        self.process.state = "test"
        test = self._run_test(self.process, "user_acceptance")
        test.action_done()
        self.assertEqual(self.process.state, "ready")

    # 6. încheierea testării cere teste finalizate
    def test_button_end_test_requires_finished_tests(self):
        self.process.state = "test"
        test = self._run_test(self.process, "internal")
        with self.assertRaises(UserError):
            self.process.button_end_test()
        self.assertEqual(self.process.state, "test")
        test.action_done()
        self.process.button_end_test()
        self.assertEqual(self.process.state, "ready")

    # 7. testul pus în așteptare poate fi reluat sau finalizat
    def test_wait_state_can_resume_or_finish(self):
        test = self._run_test(self.process, "internal")
        test.action_wait()
        test.action_run()
        self.assertEqual(test.state, "run")
        test.action_wait()
        test.action_done()
        self.assertEqual(test.state, "done")

    # 8. numărul de probleme deschise scade la închiderea problemei
    def test_count_issues_drops_when_issue_closed(self):
        test = self._run_test(self.process, "internal")
        step_test = test.test_step_ids[0]
        module = importlib.import_module("odoo.addons.deltatech_business_process.models.business_issue")
        with patch.object(module.BusinessIssue, "send_issue_mail", autospec=True):
            issue = self.env["business.issue"].create(
                {"name": "Issue", "project_id": self.project.id, "step_test_id": step_test.id}
            )
        self.assertEqual(step_test.count_issues, 1)
        issue.closed_date = issue.open_date
        issue.button_done()
        self.assertEqual(step_test.count_issues, 0)
