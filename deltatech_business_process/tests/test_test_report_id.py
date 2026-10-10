# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTestReportId(TransactionCase):
    """BUSINESS-001: each test report row has its own id, one per step test."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        area = cls.env["business.area"].create({"name": "BUSINESS-001 area"})
        project = cls.env["business.project"].create({"name": "BUSINESS-001 project"})
        process = cls.env["business.process"].create(
            {"name": "BUSINESS-001 process", "area_id": area.id, "project_id": project.id}
        )
        cls.step = cls.env["business.process.step"].create({"name": "BUSINESS-001 step", "process_id": process.id})
        StepTest = cls.env["business.process.step.test"]
        cls.step_tests = StepTest
        for name, result in (("run 1", "passed"), ("run 2", "failed")):
            test = cls.env["business.process.test"].create({"name": name, "process_id": process.id})
            cls.step_tests |= StepTest.create({"process_test_id": test.id, "step_id": cls.step.id, "result": result})
        cls.env.flush_all()

    def test_two_runs_have_distinct_rows(self):
        Report = self.env["business.process.test.report"]
        rows = Report.search([("step_id", "=", self.step.id)])
        self.assertEqual(len(rows), 2, "one report row per test run")
        self.assertEqual(set(rows.process_step_test_id.ids), set(self.step_tests.ids))
        self.assertEqual(set(rows.mapped("result")), {"passed", "failed"})
        # direct read through a fresh cache returns each run's own data
        for step_test in self.step_tests:
            row = Report.search([("process_step_test_id", "=", step_test.id)])
            self.assertEqual(len(row), 1)
            row.invalidate_recordset()
            self.assertEqual(row.read(["result", "process_step_test_id"])[0]["result"], step_test.result)
            self.assertEqual(row.process_step_test_id, step_test)
        groups = Report._read_group([("step_id", "=", self.step.id)], ["result"], ["__count"])
        self.assertEqual(dict(groups), {"passed": 1, "failed": 1})
