from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestWorkingDaysExport(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create an employee
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "hours_per_day": "8",
            }
        )

        # Create a leave type
        self.leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Test Leave",
                "type_code": "TL",
            }
        )

        # Create a validated leave for the employee
        self.leave = self.env["hr.leave"].create(
            {
                "name": "Test Leave",
                "employee_id": self.employee.id,
                "holiday_status_id": self.leave_type.id,
                "date_from": fields.Datetime.now(),
                "date_to": fields.Datetime.now() + timedelta(days=1),
            }
        )

        # Create an instance of the working days export transient model
        self.export = self.env["working.days.export"].create(
            {
                "starting_report_date": date(2024, 7, 1),
                "ending_report_date": date(2024, 7, 31),
            }
        )

    def test_do_export(self):
        # Perform the export
        result = self.export.with_context(active_ids=[self.employee.id], active_model="hr.employee").do_export()

        # Check the returned action
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "working.days.export")
        self.assertEqual(result["res_id"], self.export.id)
        self.assertEqual(result["view_mode"], "form")

        # Verify the export state
        self.assertEqual(self.export.state, "get")
        self.assertTrue(self.export.data_file)
        self.assertEqual(self.export.name, "work_day_report.xlsx")

    def test_invalid_date_range(self):
        # Set an invalid date range
        self.export.starting_report_date = date(2024, 8, 1)
        self.export.ending_report_date = date(2024, 7, 31)

        with self.assertRaises(UserError):
            self.export.with_context(active_ids=[self.employee.id], active_model="hr.employee").do_export()
