# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestKaizenProject(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Kaizen User",
                "login": "kaizen_user",
                "group_ids": [(6, 0, [cls.env.ref("deltatech_kaizen.group_kaizen_user").id])],
            }
        )
        cls.manager = cls.env["res.users"].create(
            {
                "name": "Kaizen Manager",
                "login": "kaizen_manager",
                "group_ids": [(6, 0, [cls.env.ref("deltatech_kaizen.group_kaizen_manager").id])],
            }
        )
        cls.today = fields.Date.context_today(cls.env["kaizen.project"])

    def _project(self, **vals):
        values = {
            "name": "Scrap on line 2",
            "loss_type": "scrap",
            "baseline_value": 1000.0,
            "current_value": 400.0,
        }
        values.update(vals)
        return self.env["kaizen.project"].create(values)

    def _closable_project(self, **vals):
        project = self._project(**vals)
        self.env["kaizen.why"].create({"project_id": project.id, "name": "Why? Worn tool", "is_root_cause": True})
        project.action_start_analysis()
        project.action_start_actions()
        return project

    # CA1: reference from the sequence, name required
    def test_ca1_reference_from_sequence(self):
        project = self._project()
        self.assertEqual(project.state, "draft")
        self.assertTrue(project.reference.startswith("KZN/"), project.reference)
        with self.assertRaises(IntegrityError):
            self.env["kaizen.project"].create({"loss_type": "scrap"})

    # CA2: negative loss values are refused
    def test_ca2_negative_values_refused(self):
        with self.assertRaises(ValidationError):
            self._project(baseline_value=-1.0)
        with self.assertRaises(ValidationError):
            self._project(current_value=-5.0)

    # CA3: savings = baseline - current, negative allowed
    def test_ca3_savings_and_negative_savings(self):
        project = self._project(baseline_value=1000.0, current_value=400.0)
        self.assertEqual(project.savings_monthly, 600.0)
        worse = self._project(baseline_value=100.0, current_value=250.0)
        self.assertEqual(worse.savings_monthly, -150.0)

    # CA4: annual projection is monthly x 12
    def test_ca4_annual_projection(self):
        project = self._project(baseline_value=1000.0, current_value=400.0)
        self.assertEqual(project.savings_annual, 600.0 * 12)

    # CA5: target reached only with a positive target
    def test_ca5_target_reached(self):
        reached = self._project(baseline_value=1000.0, current_value=300.0, target_value=350.0)
        self.assertTrue(reached.is_target_reached)
        not_reached = self._project(baseline_value=1000.0, current_value=400.0, target_value=350.0)
        self.assertFalse(not_reached.is_target_reached)
        no_target = self._project(baseline_value=1000.0, current_value=0.0, target_value=0.0)
        self.assertFalse(no_target.is_target_reached)

    # CA6: sixth why line refused
    def test_ca6_sixth_why_refused(self):
        project = self._project()
        for i in range(5):
            self.env["kaizen.why"].create({"project_id": project.id, "name": f"Why {i + 1}"})
        with self.assertRaises(ValidationError):
            self.env["kaizen.why"].create({"project_id": project.id, "name": "Why 6"})

    # CA7: two root causes refused
    def test_ca7_two_root_causes_refused(self):
        project = self._project()
        self.env["kaizen.why"].create({"project_id": project.id, "name": "Why 1", "is_root_cause": True})
        with self.assertRaises(ValidationError):
            self.env["kaizen.why"].create({"project_id": project.id, "name": "Why 2", "is_root_cause": True})

    # CA8: deadline before start refused
    def test_ca8_deadline_before_start_refused(self):
        with self.assertRaises(ValidationError):
            self._project(
                date_start=self.today,
                date_deadline=self.today - timedelta(days=1),
            )

    # CA9: action requires responsible and deadline
    def test_ca9_action_required_fields(self):
        project = self._project()
        with self.assertRaises(IntegrityError):
            self.env["kaizen.action"].create({"project_id": project.id, "name": "No owner", "deadline": self.today})
        with self.assertRaises(IntegrityError):
            self.env["kaizen.action"].create({"project_id": project.id, "name": "No date", "user_id": self.user.id})

    # CA10: overdue flag and done date
    def test_ca10_overdue_and_done_date(self):
        project = self._project()
        action = self.env["kaizen.action"].create(
            {
                "project_id": project.id,
                "name": "Replace tool",
                "user_id": self.user.id,
                "deadline": self.today - timedelta(days=2),
            }
        )
        self.assertTrue(action.is_overdue)
        action.action_done()
        self.assertFalse(action.is_overdue)
        self.assertEqual(action.done_date, self.today)

    # CA10 (done date is kept on repeated done)
    def test_ca10_done_date_kept(self):
        project = self._project()
        action = self.env["kaizen.action"].create(
            {"project_id": project.id, "name": "Repeat", "user_id": self.user.id, "deadline": self.today}
        )
        action.action_done()
        first = action.done_date
        action.action_done()
        self.assertEqual(action.done_date, first)

    # CA11: close refused with open actions
    def test_ca11_close_with_open_actions_refused(self):
        project = self._closable_project()
        self.env["kaizen.action"].create(
            {"project_id": project.id, "name": "Open", "user_id": self.user.id, "deadline": self.today}
        )
        with self.assertRaises(UserError):
            project.action_close()

    # CA12: close refused without root cause
    def test_ca12_close_without_root_cause_refused(self):
        project = self._project()
        project.action_start_analysis()
        project.action_start_actions()
        with self.assertRaises(UserError):
            project.action_close()

    # CA13: valid close sets state and date
    def test_ca13_close_valid_project(self):
        project = self._closable_project()
        self.env["kaizen.action"].create(
            {"project_id": project.id, "name": "Done", "user_id": self.user.id, "deadline": self.today}
        ).action_done()
        project.action_start_verification()
        project.action_close()
        self.assertEqual(project.state, "done")
        self.assertEqual(project.date_closed, self.today)

    # CA14: cancel allowed before done, refused from done
    def test_ca14_cancel(self):
        project = self._project()
        project.action_start_analysis()
        project.action_cancel()
        self.assertEqual(project.state, "cancelled")
        done = self._closable_project()
        done.action_close()
        with self.assertRaises(UserError):
            done.action_cancel()

    # CA15: user cannot delete, manager can
    def test_ca15_delete_rights(self):
        project = self._project()
        with self.assertRaises(AccessError):
            project.with_user(self.user).unlink()
        project.with_user(self.manager).unlink()
        self.assertFalse(project.exists())

    # Edge: deleting a project cascades to its lines
    def test_edge_cascade_delete(self):
        project = self._project()
        self.env["kaizen.why"].create({"project_id": project.id, "name": "Why 1"})
        self.env["kaizen.ishikawa.cause"].create(
            {"project_id": project.id, "category": "machine", "name": "Blade wear"}
        )
        self.env["kaizen.action"].create(
            {"project_id": project.id, "name": "Sharpen", "user_id": self.user.id, "deadline": self.today}
        )
        project.unlink()
        self.assertFalse(self.env["kaizen.why"].search_count([("project_id", "=", project.id)]))
        self.assertFalse(self.env["kaizen.ishikawa.cause"].search_count([("project_id", "=", project.id)]))
        self.assertFalse(self.env["kaizen.action"].search_count([("project_id", "=", project.id)]))
