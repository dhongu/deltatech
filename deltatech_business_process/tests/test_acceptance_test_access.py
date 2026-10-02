# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAcceptanceTestAccess(TransactionCase):
    """BUSINESS-003: the public start_user_acceptance_test creates the test as superuser, it must
    check the caller and the process access first."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env["res.company"].create({"name": "BUSINESS-003 other company"})
        cls.end_user = new_test_user(
            cls.env,
            login="bp003_end_user",
            groups="base.group_user,deltatech_business_process.group_business_end_user",
            company_id=cls.company.id,
            company_ids=[Command.set(cls.company.ids)],
        )
        cls.other_user = new_test_user(
            cls.env,
            login="bp003_other_user",
            groups="base.group_user,deltatech_business_process.group_business_end_user",
        )
        cls.internal_user = new_test_user(cls.env, login="bp003_internal", groups="base.group_user")
        cls.area = cls.env["business.area"].create({"name": "BUSINESS-003 area"})
        cls.project = cls.env["business.project"].create({"name": "BUSINESS-003", "company_id": cls.company.id})
        cls.other_project = cls.env["business.project"].create(
            {"name": "BUSINESS-003 other", "company_id": cls.other_company.id}
        )
        cls.process = cls._create_process("Visible", cls.project)
        cls.hidden_process = cls._create_process("Hidden", cls.project, allowed_user_ids=cls.other_user.ids)
        cls.other_company_process = cls._create_process("Other company", cls.other_project)

    @classmethod
    def _create_process(cls, name, project, **values):
        process = cls.env["business.process"].create(
            {
                "name": name,
                "area_id": cls.area.id,
                "project_id": project.id,
                **values,
            }
        )
        cls.env["business.process.step"].create({"name": f"{name} step", "process_id": process.id})
        return process

    def _acceptance_tests(self, process):
        return self.env["business.process.test"].search(
            [("process_id", "=", process.id), ("scope", "=", "user_acceptance")]
        )

    def test_end_user_starts_acceptance_test(self):
        test = self.process.with_user(self.end_user).start_user_acceptance_test()
        self.assertEqual(len(test), 1)
        self.assertEqual(test.env.uid, self.end_user.id)
        self.assertFalse(test.env.su, "The test is returned in the caller's environment")
        self.assertEqual(test.process_id, self.process)
        self.assertTrue(test.test_step_ids)

    def test_end_user_opens_acceptance_tests(self):
        action = self.process.with_user(self.end_user).action_view_acceptance_tests()
        self.assertEqual(action["res_id"], self._acceptance_tests(self.process).id)

    def test_hidden_process_is_refused(self):
        with self.assertRaises(AccessError):
            self.hidden_process.with_user(self.end_user).start_user_acceptance_test()
        self.assertFalse(self._acceptance_tests(self.hidden_process))

    def test_process_of_another_company_is_refused(self):
        with self.assertRaises(AccessError):
            self.other_company_process.with_user(self.end_user).start_user_acceptance_test()
        self.assertFalse(self._acceptance_tests(self.other_company_process))

    def test_user_without_business_group_is_refused(self):
        with self.assertRaises(AccessError):
            self.process.with_user(self.internal_user).start_user_acceptance_test()
        self.assertFalse(self._acceptance_tests(self.process))
