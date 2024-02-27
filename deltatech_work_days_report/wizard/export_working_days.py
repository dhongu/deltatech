from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class WorkingDaysExport(models.TransientModel):
    _name = "working.days.export"
    _description = "Working Days Export"

    starting_report_date = fields.Date("From", required=True)
    ending_report_date = fields.Date("To", required=True)
    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")

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
                        row.append("ABS")  # Employee was on vacation
                    else:
                        row.append(employee.hours_per_day)
                        total_hours = total_hours + int(employee.hours_per_day)
                        meal_vouchers_number += 1
            row.append(total_hours)
            row.append(meal_vouchers_number)
            matrix.append(row)
