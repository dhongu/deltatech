import base64
from datetime import timedelta
from io import BytesIO

import xlwt

from odoo import _, fields, models
from odoo.exceptions import UserError


class WorkingDaysExport(models.TransientModel):
    _name = "working.days.export"
    _description = "Working Days Export"

    starting_report_date = fields.Date("From", required=True)
    ending_report_date = fields.Date("To", required=True)
    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")
    data_file = fields.Binary(string="File", readonly=True)
    name = fields.Char(string="File Name", readonly=True)

    def do_export(self):
        active_ids = self.env.context.get("active_ids", [])
        active_model = self.env.context.get("active_model", "hr.employee")
        employees = self.env[active_model].browse(active_ids)

        if self.starting_report_date > self.ending_report_date:
            raise UserError(_("Please make sure the second date is after the first"))

        headers = ["Nr.", "Name", "Norma"]
        footer = ["Total number of hours", "Meal Vouchers"]
        dates_between = []
        dates_between_days = []
        current_date = self.starting_report_date
        while current_date <= self.ending_report_date:
            dates_between.append(current_date)
            dates_between_days.append(current_date.day)
            current_date += timedelta(days=1)

        matrix = [headers + dates_between_days + footer]
        for employee in employees:
            total_hours = 0
            meal_vouchers_number = 0
            row = [employee.id, employee.name, employee.hours_per_day]
            for date in dates_between:
                if date.weekday() in [5, 6]:
                    row.append(" ")
                else:
                    holiday = self.env["hr.leave"].search(
                        [
                            ("employee_id", "=", employee.id),
                            ("state", "=", "validate"),  # Assuming you want only validated leaves
                            ("date_from", "<=", date),
                            ("date_to", ">=", date),
                        ]
                    )
                    if holiday:
                        if holiday.holiday_status_id.type_code:
                            row.append(holiday.holiday_status_id.type_code)
                        else:
                            row.append("ABS")  # Employee was on vacation
                    else:
                        row.append(employee.hours_per_day)
                        total_hours = total_hours + int(employee.hours_per_day)
                        meal_vouchers_number += 1
            row.append(total_hours)
            row.append(meal_vouchers_number)
            matrix.append(row)

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("Working Days Report")

        # Write matrix data to the Excel sheet
        for i, row in enumerate(matrix):
            for j, value in enumerate(row):
                sheet.write(i, j, value)

        # Save the Excel file to a BytesIO buffer
        output_buffer = BytesIO()
        workbook.save(output_buffer)
        output_buffer.seek(0)

        # Set the data_file field with the content of the file
        self.write(
            {"state": "get", "name": "work_day_report.xlsx", "data_file": base64.b64encode(output_buffer.getvalue())}
        )
        output_buffer.close()

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }
