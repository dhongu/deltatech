import base64
import calendar
from datetime import timedelta
from io import BytesIO

import xlsxwriter

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

        headers = [_("Nr."), _("Name"), _("Norma")]
        footer = [_("Total number of hours"), _("Meal Vouchers")]
        dates_between = []
        dates_between_days = []
        current_date = self.starting_report_date
        while current_date <= self.ending_report_date:
            dates_between.append(current_date)
            dates_between_days.append(current_date.day)
            current_date += timedelta(days=1)

        code_types = []
        time_off_types = self.env["hr.leave.type"].search([])
        for time_type in time_off_types:
            code_types.append(time_type.type_code)
        matrix = [headers + dates_between_days + code_types + footer]
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
                            (
                                "state",
                                "=",
                                "validate",
                            ),  # Assuming you want only validated leaves
                            ("date_from", "<=", date),
                            ("date_to", ">=", date),
                        ]
                    )
                    if holiday:
                        row.append(holiday.holiday_status_id.type_code)
                    else:
                        row.append(employee.hours_per_day)
                        total_hours = total_hours + int(employee.hours_per_day)
                        meal_vouchers_number += 1
            for code in code_types:
                count = 0
                for cell in row:
                    if cell == code:
                        count += 1
                row.append(count)

            row.append(total_hours)
            row.append(meal_vouchers_number)
            matrix.append(row)

        output_buffer = BytesIO()
        workbook = xlsxwriter.Workbook(output_buffer)
        worksheet = workbook.add_worksheet("Working Days Report")
        bold = workbook.add_format({"bold": True, "align": "center", "valign": "vcenter"})
        row_length = len(matrix[1])
        result = ""

        while row_length > 0:
            row_length, remainder = divmod(row_length - 1, 26)
            result = chr(65 + remainder) + result
        worksheet.merge_range("A1:" + result + "2", _("Attendance Sheet"), bold)
        worksheet.merge_range(
            "A3:" + result + "3",
            _("Month:")
            + calendar.month_name[self.starting_report_date.month]
            + "-"
            + str(self.starting_report_date.year),
            bold,
        )
        bold = workbook.add_format({"align": "center", "valign": "vcenter"})
        worksheet.merge_range("A4:C4", _("Employee"), bold)
        dates_length = len(dates_between_days) + 3
        result = ""
        while dates_length > 0:
            dates_length, remainder = divmod(dates_length - 1, 26)
            result = chr(65 + remainder) + result
        worksheet.merge_range("D4:" + result + "4", _("Days"), bold)
        if result[1] != "Z":
            letter = chr(ord(result[1]) + 1)
            new_letter = result[0] + letter
            result = new_letter
        else:
            letter = chr(ord(result[0]) + 1)
            result = letter + "A"
        start_point = result
        result = ""
        codes_length = len(dates_between_days) + 3 + len(code_types)
        while codes_length > 0:
            codes_length, remainder = divmod(codes_length - 1, 26)
            result = chr(65 + remainder) + result
        worksheet.merge_range(start_point + "4:" + result + "4", _("Time Off Codes"), bold)
        # Write matrix data to the Excel sheet
        for i, row in enumerate(matrix):
            for j, value in enumerate(row):
                worksheet.write(i + 4, j, value)

        # Close the workbook
        workbook.close()

        # Set the data_file field with the content of the file
        self.write(
            {
                "state": "get",
                "name": "work_day_report.xlsx",
                "data_file": base64.b64encode(output_buffer.getvalue()),
            }
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
