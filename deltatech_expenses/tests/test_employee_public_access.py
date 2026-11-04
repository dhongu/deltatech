# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEmployeePublicAccess(TransactionCase):
    """Câmpurile adăugate pe hr.employee (și pe hr.version, moștenite prin _inherits) care lipsesc din
    hr.employee.public trebuie să aibă groups, altfel intră în prefetch-ul utilizatorilor fără drept HR
    (website, POS) și citirea angajatului dă AccessError."""

    def test_private_fields_have_groups(self):
        public_fields = self.env["hr.employee.public"]._fields
        for field in self.env["hr.employee"]._fields.values():
            if "deltatech_expenses" not in field._modules or field.name in public_fields:
                continue
            with self.subTest(field=field.name):
                self.assertTrue(field.groups, f"hr.employee.{field.name} is private but has no groups")

    def test_non_hr_user_reads_employee(self):
        user = new_test_user(self.env, login="deltatech_expenses_public_user", groups="base.group_user")
        employee = self.env["hr.employee"].create({"name": "deltatech_expenses public employee", "user_id": user.id})
        employee_as_user = employee.with_user(user)
        employee_as_user.invalidate_recordset()
        self.assertEqual(employee_as_user.name, "deltatech_expenses public employee")
        self.assertEqual(user.employee_id.with_user(user).name, "deltatech_expenses public employee")
