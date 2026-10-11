# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from datetime import datetime, timedelta

import pytz


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

    def add(self, day, nb_days):
        """The day after `nb_days` working days counted from the day after `day`."""
        while nb_days > 0:
            day += timedelta(days=1)
            if self.is_working(day):
                nb_days -= 1
        return day

    def next_working(self, day):
        """`day` itself if it is a working day, else the first working day after it."""
        # a year without any working day is a configuration error: stop instead of looping forever
        limit = day + timedelta(days=366)
        while not self.is_working(day) and day < limit:
            day += timedelta(days=1)
        return day
