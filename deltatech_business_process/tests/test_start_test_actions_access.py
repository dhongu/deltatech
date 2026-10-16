# © 2026 Deltatech
from contextlib import suppress

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

ACTIONS = (
    "deltatech_business_process.action_start_internal_test",
    "deltatech_business_process.action_start_integration_test",
)


@tagged("post_install", "-at_install")
class TestStartTestActionsAccess(TransactionCase):
    """No role creates a test on a process it cannot access, neither through the
    Start Internal/Integration Test actions nor by calling the methods directly."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.company
        other_company = cls.env["res.company"].create({"name": "BUSINESS-009 other company"})
        cls.users = {
            role: new_test_user(
                cls.env,
                login=f"bp009_{role}",
                groups=f"base.group_user,deltatech_business_process.group_business_{group}",
                company_id=company.id,
                company_ids=[Command.set(company.ids)],
            )
            for role, group in (("end", "end_user"), ("resp", "process_responsible"), ("mgr", "process_manager"))
        }
        cls.other_user = new_test_user(cls.env, login="bp009_other", groups="base.group_user")
        area = cls.env["business.area"].create({"name": "BUSINESS-009 area"})
        project = cls.env["business.project"].create({"name": "BUSINESS-009", "company_id": company.id})
        other_project = cls.env["business.project"].create({"name": "BUSINESS-009 B", "company_id": other_company.id})
        cls.hidden = cls.env["business.process"].create(
            {"name": "Hidden", "area_id": area.id, "project_id": project.id, "allowed_user_ids": cls.other_user.ids}
        )
        cls.visible = cls.env["business.process"].create(
            {"name": "Visible", "area_id": area.id, "project_id": project.id}
        )
        cls.foreign = cls.env["business.process"].create(
            {"name": "Foreign", "area_id": area.id, "project_id": other_project.id}
        )

    def _tests(self, process):
        return self.env["business.process.test"].search([("process_id", "=", process.id)])

    def _run(self, user, xmlid, process):
        action = (
            self.env.ref(xmlid)
            .with_user(user)
            .with_context(active_model="business.process", active_ids=process.ids, active_id=process.id)
        )
        return action.run()

    def test_no_test_on_inaccessible_process(self):
        for role, user in self.users.items():
            targets = [self.foreign] + ([] if role == "mgr" else [self.hidden])
            for process in targets:
                for xmlid in ACTIONS:
                    # refuzul face rollback la savepoint, ca o cerere RPC
                    with suppress(AccessError), self.env.cr.savepoint():
                        self._run(user, xmlid, process)
                    self.assertFalse(self._tests(process), f"{role} {xmlid} {process.name}")
                for method in ("start_internal_test", "start_integration_test"):
                    # refuzul face rollback la savepoint, ca o cerere RPC
                    with suppress(AccessError), self.env.cr.savepoint():
                        getattr(process.with_user(user), method)()
                    self.assertFalse(self._tests(process), f"{role} {method} {process.name}")

    def test_manager_starts_tests_through_actions(self):
        for xmlid in ACTIONS:
            self._run(self.users["mgr"], xmlid, self.visible)
        self.assertEqual(sorted(self._tests(self.visible).mapped("scope")), ["integration", "internal"])
