# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from collections import defaultdict
from datetime import date, datetime

from odoo import api, fields, models

from ..models.safety_event import LOST_TIME_TYPES

LTIFR_BASE = 1_000_000


class SafetyIndicator(models.TransientModel):
    _name = "deltatech.safety.indicator"
    _description = "Safety Indicators"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    year = fields.Integer(required=True, default=lambda self: fields.Date.context_today(self).year)

    near_miss_count = fields.Integer(compute="_compute_indicators", string="Near misses")
    lost_time_count = fields.Integer(
        compute="_compute_indicators",
        string="Lost-time injuries",
        help="Events of type Lost-time injury or Fatal, without commuting accidents.",
    )
    commute_count = fields.Integer(compute="_compute_indicators", string="Commuting accidents")
    hours_worked = fields.Float(
        compute="_compute_indicators",
        help="Sum of worked hours from Attendances of the company's employees in the year. "
        "People without attendance records (contractors) are not included.",
    )
    missing_months = fields.Char(compute="_compute_indicators", string="Months without hours worked")
    ltifr = fields.Float(
        compute="_compute_indicators",
        string="LTIFR",
        digits=(16, 2),
        help="Lost-time injuries x 1,000,000 / hours worked. Empty while a past month has no hours worked.",
    )
    last_injury_date = fields.Date(compute="_compute_indicators")
    days_without_accident = fields.Integer(
        compute="_compute_indicators",
        help="Days since the last injury (Injury, Lost-time injury or Fatal). Empty when no injury is recorded.",
    )

    @api.depends("company_id", "year")
    def _compute_indicators(self):
        Event = self.env["deltatech.safety.event"]
        today = fields.Date.context_today(self)
        for indicator in self:
            values = {
                "near_miss_count": 0,
                "lost_time_count": 0,
                "commute_count": 0,
                "hours_worked": 0.0,
                "missing_months": False,
                "ltifr": False,
                "last_injury_date": False,
                "days_without_accident": False,
            }
            company = indicator.company_id
            year = indicator.year
            if company and year:
                events = Event.search(
                    [
                        ("company_id", "=", company.id),
                        ("date", ">=", date(year, 1, 1)),
                        ("date", "<", date(year + 1, 1, 1)),
                    ]
                )
                lost_time = events.filtered(lambda e: e.event_type in LOST_TIME_TYPES and not e.is_commute)
                values["near_miss_count"] = len(events.filtered(lambda e: e.event_type == "near_miss"))
                values["lost_time_count"] = len(lost_time)
                values["commute_count"] = len(events.filtered(lambda e: e.is_injury and e.is_commute))

                hours_by_month = indicator._hours_by_month(company, year)
                hours = sum(hours_by_month.values())
                past_months = [month for month in range(1, 13) if date(year, month, 1) <= today]
                missing = [month for month in past_months if not hours_by_month.get(month)]
                values["hours_worked"] = hours
                if missing:
                    values["missing_months"] = ", ".join(f"{month:02d}/{year}" for month in missing)
                elif hours:
                    values["ltifr"] = round(len(lost_time) * LTIFR_BASE / hours, 2)

                last_injury = Event.search(
                    [("company_id", "=", company.id), ("is_injury", "=", True), ("date", "<=", today)],
                    order="date desc, id desc",
                    limit=1,
                )
                if last_injury:
                    values["last_injury_date"] = last_injury.date
                    values["days_without_accident"] = (today - last_injury.date).days
            indicator.update(values)

    def _hours_by_month(self, company, year):
        """Worked hours of the company's employees, per month of check-in (UTC)."""
        attendances = (
            self.env["hr.attendance"]
            .sudo()
            .search(
                [
                    ("employee_id.company_id", "=", company.id),
                    ("check_in", ">=", datetime(year, 1, 1)),
                    ("check_in", "<", datetime(year + 1, 1, 1)),
                ]
            )
        )
        hours_by_month = defaultdict(float)
        for attendance in attendances:
            hours_by_month[attendance.check_in.month] += attendance.worked_hours
        return hours_by_month
