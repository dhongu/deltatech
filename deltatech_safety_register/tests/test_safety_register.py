from datetime import date, datetime, timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSafetyRegister(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Event = cls.env["deltatech.safety.event"]
        cls.Indicator = cls.env["deltatech.safety.indicator"]
        group_user = cls.env.ref("base.group_user")
        officer_group = cls.env.ref("deltatech_safety_register.group_safety_officer")
        manager_group = cls.env.ref("deltatech_safety_register.group_safety_manager")
        cls.officer = cls._create_user("safety_officer", [group_user, officer_group], cls.company)
        cls.manager = cls._create_user("safety_manager", [group_user, manager_group], cls.company)
        cls.plain_user = cls._create_user("safety_plain", [group_user], cls.company)
        cls.employee = cls.env["hr.employee"].create({"name": "Safety Test Employee", "company_id": cls.company.id})
        cls.today = fields.Date.context_today(cls.Event)

    @classmethod
    def _create_user(cls, login, groups, company):
        return (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": login,
                    "login": login,
                    "email": f"{login}@example.com",
                    "company_id": company.id,
                    "company_ids": [(6, 0, company.ids)],
                    "group_ids": [(6, 0, [g.id for g in groups])],
                }
            )
        )

    def _event(self, event_type="near_miss", **vals):
        values = {"event_type": event_type, "date": self.today, "description": "Test event"}
        if event_type in ("injury", "lost_time_injury", "fatal") and not any(
            key in vals for key in ("employee_id", "partner_id", "injured_name")
        ):
            values["employee_id"] = self.employee.id
        values.update(vals)
        return self.Event.with_user(self.officer).create(values)

    def _attendances(self, year, months, hours=8):
        Attendance = self.env["hr.attendance"]
        for month in months:
            check_in = datetime(year, month, 3, 6, 0)
            Attendance.create(
                {
                    "employee_id": self.employee.id,
                    "check_in": check_in,
                    "check_out": check_in + timedelta(hours=hours),
                }
            )

    def _indicator(self, year):
        return self.Indicator.with_user(self.officer).create({"year": year, "company_id": self.company.id})

    def test_ca1_near_miss_reported_with_reference(self):
        """CA1: a new near miss is Reported and gets the next SAF/<year>/NNNN reference."""
        first = self._event()
        second = self._event()
        self.assertEqual(first.state, "reported")
        year = fields.Date.context_today(first).year
        self.assertRegex(first.name, rf"^SAF/{year}/\d{{4}}$")
        self.assertEqual(int(second.name.rsplit("/", 1)[1]), int(first.name.rsplit("/", 1)[1]) + 1)

    def test_ca2_injury_requires_injured_person(self):
        """CA2: an injury without employee, partner or name cannot be saved."""
        with self.assertRaises(ValidationError):
            self.Event.with_user(self.officer).create({"event_type": "lost_time_injury", "date": self.today})
        by_employee = self._event("lost_time_injury", employee_id=self.employee.id)
        by_name = self._event("lost_time_injury", injured_name="Visitor X")
        by_partner = self._event("injury", partner_id=self.env["res.partner"].create({"name": "Contractor"}).id)
        self.assertEqual(by_employee.department_id, self.employee.department_id)
        self.assertTrue(by_name.is_injury and by_partner.is_injury)

    def test_ca3_action_creates_activity(self):
        """CA3: a corrective action schedules one activity for its responsible user with its deadline."""
        event = self._event()
        deadline = self.today + timedelta(days=7)
        action = (
            self.env["deltatech.safety.action"]
            .with_user(self.officer)
            .create(
                {
                    "event_id": event.id,
                    "description": "Fix the guard rail",
                    "user_id": self.manager.id,
                    "deadline": deadline,
                }
            )
        )
        activities = event.activity_ids.filtered(lambda a: a.user_id == self.manager)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.date_deadline, deadline)
        self.assertEqual(action.activity_id, activities)

        # a deadline in the past schedules the activity for today
        past = (
            self.env["deltatech.safety.action"]
            .with_user(self.officer)
            .create(
                {"event_id": event.id, "description": "Late", "user_id": self.officer.id, "deadline": date(2020, 1, 1)}
            )
        )
        self.assertEqual(past.activity_id.date_deadline, self.today)

    def test_ca4_close_requires_actions_done(self):
        """CA4: Close is refused while an action is open; afterwards it sets Closed and the date."""
        event = self._event()
        action = (
            self.env["deltatech.safety.action"]
            .with_user(self.officer)
            .create({"event_id": event.id, "description": "Train the team", "user_id": self.officer.id})
        )
        with self.assertRaises(UserError):
            event.with_user(self.officer).action_close()
        self.assertEqual(event.state, "reported")

        action.with_user(self.officer).action_done()
        self.assertEqual(action.state, "done")
        self.assertFalse(action.activity_id)
        self.assertFalse(event.activity_ids)

        event.with_user(self.officer).action_close()
        self.assertEqual(event.state, "closed")
        self.assertEqual(event.closed_date, self.today)
        # second press is a no-op
        event.with_user(self.officer).action_close()
        self.assertEqual(event.state, "closed")

    def test_ca5_ltifr_from_attendance(self):
        """CA5: LTIFR = lost-time injuries x 1,000,000 / hours worked from attendances."""
        year = self.today.year - 1
        self._attendances(year, range(1, 13))
        for day in (date(year, 2, 1), date(year, 6, 1)):
            self._event("lost_time_injury", date=day)
        for _i in range(5):
            self._event("near_miss", date=date(year, 4, 1))
        self._event("incident", date=date(year, 4, 1))

        indicator = self._indicator(year)
        self.assertEqual(indicator.hours_worked, 96)
        self.assertEqual(indicator.lost_time_count, 2)
        self.assertEqual(indicator.near_miss_count, 5)
        self.assertFalse(indicator.missing_months)
        self.assertAlmostEqual(indicator.ltifr, round(2 * 1_000_000 / 96, 2))

    def test_ca6_missing_hours_blocks_ltifr(self):
        """CA6: a past month without attendance leaves LTIFR empty and names the month."""
        year = self.today.year - 1
        self._attendances(year, [m for m in range(1, 13) if m != 3])
        self._event("lost_time_injury", date=date(year, 5, 1))
        indicator = self._indicator(year)
        self.assertFalse(indicator.ltifr)
        self.assertEqual(indicator.missing_months, f"03/{year}")

    def test_ca7_days_without_accident(self):
        """CA7: days since the last injury; near misses and incidents do not reset the counter."""
        indicator = self._indicator(self.today.year)
        self.assertFalse(indicator.last_injury_date)
        self.assertFalse(indicator.days_without_accident)

        self._event("injury", date=self.today - timedelta(days=40))
        self._event("lost_time_injury", date=self.today - timedelta(days=10))
        self._event("near_miss", date=self.today - timedelta(days=2))
        self._event("incident", date=self.today - timedelta(days=1))
        indicator = self._indicator(self.today.year)
        self.assertEqual(indicator.last_injury_date, self.today - timedelta(days=10))
        self.assertEqual(indicator.days_without_accident, 10)

    def test_ca8_access_rights(self):
        """CA8: users outside the safety groups and users of another company see no events."""
        event = self._event()
        with self.assertRaises(AccessError):
            self.Event.with_user(self.plain_user).search([])

        company_b = self.env["res.company"].create({"name": "Safety Company B"})
        officer_group = self.env.ref("deltatech_safety_register.group_safety_officer")
        officer_b = self._create_user("safety_officer_b", [self.env.ref("base.group_user"), officer_group], company_b)
        events_b = self.Event.with_user(officer_b).with_context(allowed_company_ids=company_b.ids).search([])
        self.assertNotIn(event, events_b)
        self.assertFalse(events_b)

    def test_ca9_closed_event_locked_for_officer(self):
        """CA9: an officer cannot edit a closed event; a manager can; closed events cannot be deleted."""
        event = self._event()
        event.with_user(self.officer).action_close()
        with self.assertRaises(UserError):
            event.with_user(self.officer).write({"description": "Changed"})
        event.with_user(self.manager).write({"description": "Changed by manager"})
        self.assertEqual(event.description, "Changed by manager")
        with self.assertRaises(UserError):
            event.with_user(self.manager).unlink()

        reported = self._event()
        with self.assertRaises(AccessError):
            reported.with_user(self.officer).unlink()
        reported.with_user(self.manager).unlink()
        self.assertFalse(reported.exists())

    def test_ca10_commute_excluded_from_ltifr(self):
        """CA10: commuting accidents are counted apart and not in LTIFR."""
        year = self.today.year - 1
        self._attendances(year, range(1, 13))
        self._event("lost_time_injury", date=date(year, 3, 1))
        self._event("lost_time_injury", date=date(year, 3, 2), is_commute=True)
        indicator = self._indicator(year)
        self.assertEqual(indicator.lost_time_count, 1)
        self.assertEqual(indicator.commute_count, 1)
        self.assertAlmostEqual(indicator.ltifr, round(1_000_000 / 96, 2))

    def test_ca11_export_columns(self):
        """CA11: the event list exports reference, date, type, injured person, commute flag, state, open actions."""
        event = self._event("lost_time_injury", is_commute=True)
        self.officer.group_ids = [(4, self.env.ref("base.group_allow_export").id)]
        fields_to_export = ["name", "date", "event_type", "employee_id", "is_commute", "state", "open_action_count"]
        rows = event.with_user(self.officer).export_data(fields_to_export)["datas"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], event.name)
        self.assertEqual(rows[0][3], self.employee.name)
