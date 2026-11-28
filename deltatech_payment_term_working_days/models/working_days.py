# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from datetime import datetime, timedelta

import pytz

from odoo.exceptions import UserError


class WorkingDays:
    """Working days of a company: the days of its working schedule minus its public holidays.

    The public holidays are the global time off (no resource) of the company or of
    every company, on the working schedule of the company or on every schedule.
    Without a working schedule, Monday to Friday are working days. The holidays
    are read one year at a time, when a day of that year is first asked for.
    """

    def __init__(self, env, company):
        self.env = env
        self.company = company
        self.calendar = company.resource_calendar_id
        self.tz = pytz.timezone(self.calendar.tz or company.partner_id.tz or env.user.tz or "UTC")
        self._holidays = {}

    def _year_holidays(self, year):
        if year not in self._holidays:
            start = datetime(year, 1, 1) - timedelta(days=1)
            stop = datetime(year, 12, 31, 23, 59, 59) + timedelta(days=1)
            # sudo: the time off is configured by HR, the due dates are computed by anyone invoicing
            leaves = (
                self.env["resource.calendar.leaves"]
                .sudo()
                .search(
                    [
                        ("resource_id", "=", False),
                        ("time_type", "=", "leave"),
                        ("company_id", "in", [False, self.company.id]),
                        ("calendar_id", "in", [False, self.calendar.id]),
                        ("date_from", "<=", stop),
                        ("date_to", ">=", start),
                    ]
                )
            )
            days = set()
            for leave in leaves:
                day = pytz.utc.localize(leave.date_from).astimezone(self.tz).date()
                last = pytz.utc.localize(leave.date_to).astimezone(self.tz).date()
                while day <= last:
                    days.add(day)
                    day += timedelta(days=1)
            self._holidays[year] = days
        return self._holidays[year]

    def is_working(self, day):
        if self.calendar:
            if not self.calendar._works_on_date(day):
                return False
        elif day.weekday() >= 5:
            return False
        return day not in self._year_holidays(day.year)

    def _no_working_day_error(self):
        return UserError(
            self.env._(
                "No working day could be found in a year for the company %(company)s. "
                "Check its working schedule (it has no working time) and its public holidays.",
                company=self.company.display_name,
            )
        )

    def add(self, day, nb_days):
        """The day after `nb_days` working days counted from the day after `day`."""
        # a stretch of a year without any working day is a configuration error: stop instead of looping forever
        idle = 0
        while nb_days > 0:
            day += timedelta(days=1)
            if self.is_working(day):
                nb_days -= 1
                idle = 0
            else:
                idle += 1
                if idle > 366:
                    raise self._no_working_day_error()
        return day

    def next_working(self, day):
        """`day` itself if it is a working day, else the first working day after it."""
        limit = day + timedelta(days=366)
        while not self.is_working(day):
            if day >= limit:
                raise self._no_working_day_error()
            day += timedelta(days=1)
        return day
