# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCompanyRules(TransactionCase):
    """BUSINESS-002: the SQL reports, Open Issue and migrations follow the project company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "BUSINESS-002 company B"})
        cls.admin_a = new_test_user(
            cls.env,
            login="bp002_admin_a",
            groups="base.group_user,deltatech_business_process.group_business_process_manager",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        cls.end_user_a = new_test_user(
            cls.env,
            login="bp002_end_user_a",
            groups="base.group_user,deltatech_business_process.group_business_end_user",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        area = cls.env["business.area"].create({"name": "BUSINESS-002 area"})
        cls.data = {}
        for key, company in (("a", cls.company_a), ("b", cls.company_b)):
            project = cls.env["business.project"].create({"name": f"BUSINESS-002 {key}", "company_id": company.id})
            process = cls.env["business.process"].create(
                {"name": f"BUSINESS-002 process {key}", "area_id": area.id, "project_id": project.id}
            )
            step = cls.env["business.process.step"].create({"name": f"step {key}", "process_id": process.id})
            test = cls.env["business.process.test"].create({"name": f"test {key}", "process_id": process.id})
            step_test = cls.env["business.process.step.test"].create({"process_test_id": test.id, "step_id": step.id})
            open_issue = cls.env["business.open.issue"].create({"name": f"open issue {key}", "project_id": project.id})
            migration = cls.env["business.migration"].create({"name": f"migration {key}", "project_id": project.id})
            migration_test = cls.env["business.migration.test"].create(
                {"name": f"migration test {key}", "migration_id": migration.id}
            )
            cls.data[key] = {
                "process": process,
                "step": step,
                "step_test": step_test,
                "open_issue": open_issue,
                "migration": migration,
                "migration_test": migration_test,
            }
        cls.env.flush_all()

    def _report_processes(self, user, model):
        return self.env[model].with_user(user).search([]).process_id

    def test_reports_follow_company(self):
        for user in (self.admin_a, self.end_user_a):
            for model in ("business.process.report", "business.process.test.report"):
                processes = self._report_processes(user, model)
                self.assertIn(self.data["a"]["process"], processes, f"{model} / {user.login}")
                self.assertNotIn(self.data["b"]["process"], processes, f"{model} / {user.login}")

    def test_report_company_field(self):
        report = self.env["business.process.report"].search([("step_id", "=", self.data["b"]["step"].id)])
        self.assertEqual(report.company_id, self.company_b)
        report = self.env["business.process.test.report"].search(
            [("process_step_test_id", "=", self.data["b"]["step_test"].id)]
        )
        self.assertEqual(report.company_id, self.company_b)

    def test_open_issue_follows_company(self):
        OpenIssue = self.env["business.open.issue"].with_user(self.admin_a)
        issues = OpenIssue.search([("name", "like", "open issue")])
        self.assertIn(self.data["a"]["open_issue"], issues)
        self.assertNotIn(self.data["b"]["open_issue"], issues)
        other = self.data["b"]["open_issue"].with_user(self.admin_a)
        with self.assertRaises(AccessError):
            other.read(["name"])
        with self.assertRaises(AccessError):
            other.write({"name": "changed"})

    def test_migrations_follow_company(self):
        for model, key in (("business.migration", "migration"), ("business.migration.test", "migration_test")):
            records = self.env[model].with_user(self.end_user_a).search([])
            self.assertIn(self.data["a"][key], records, model)
            self.assertNotIn(self.data["b"][key], records, model)

    def test_user_with_both_companies_sees_both(self):
        self.admin_a.company_ids = [Command.link(self.company_b.id)]
        env = self.env(user=self.admin_a, context={"allowed_company_ids": [self.company_a.id, self.company_b.id]})
        processes = env["business.process.report"].search([]).process_id
        self.assertIn(self.data["b"]["process"], processes)
        self.assertIn(self.data["b"]["open_issue"], env["business.open.issue"].search([]))
