from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("deltatech_ledger", "post_install", "-at_install")
class TestLedger(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ledger = cls.env["ledger.ledger"]
        group_user = cls.env.ref("base.group_user")
        group_manager = cls.env.ref("deltatech_ledger.group_ledger_manager")
        cls.user = cls.env["res.users"].create(
            {"name": "Ledger user", "login": "ledger_user", "group_ids": [(6, 0, [group_user.id])]}
        )
        cls.manager = cls.env["res.users"].create(
            {"name": "Ledger manager", "login": "ledger_manager", "group_ids": [(6, 0, [group_manager.id])]}
        )

    def _record(self, name, date, **kwargs):
        # explicit names keep the tests in their own year, away from the real register
        vals = {"name": name, "record_type": "entry", "record_date": date}
        vals.update(kwargs)
        return self.Ledger.create(vals)

    def _cancel(self, records, reason="Test"):
        self.env["ledger.cancel.wizard"].create({"ledger_ids": [(6, 0, records.ids)], "reason": reason}).action_cancel()

    # --- creation and numbering ---------------------------------------------------------

    def test_create_ledger_entry(self):
        ledger_entry = self.Ledger.create({"record_type": "entry", "record_short_description": "Test Entry"})
        self.assertEqual(ledger_entry.state, "active")
        self.assertEqual(ledger_entry.record_date, fields.Date.context_today(ledger_entry))
        self.assertEqual(ledger_entry.company_id, self.env.company)

    def test_create_ledger_exit(self):
        ledger_exit = self.Ledger.create({"record_type": "exit"})
        self.assertEqual(ledger_exit.state, "active")
        self.assertEqual(ledger_exit.record_type, "exit")

    def test_sequence_is_unique_and_increasing(self):
        first, second = self.Ledger.create([{"record_type": "entry"}, {"record_type": "exit"}])
        self.assertNotEqual(first.name, "New")
        self.assertLess(first.name, second.name)

    def test_sequence_restarts_every_year(self):
        sequence = self.env["ir.sequence"]
        self.assertEqual(sequence.next_by_code("ledger.ledger", sequence_date="2098-05-01"), "2098/00001")
        self.assertEqual(sequence.next_by_code("ledger.ledger", sequence_date="2098-06-01"), "2098/00002")
        self.assertEqual(sequence.next_by_code("ledger.ledger", sequence_date="2099-01-02"), "2099/00001")

    def test_copy_gets_new_number_and_active_state(self):
        original = self.Ledger.create({"record_type": "entry", "document_number": "A-1"})
        self._cancel(original)
        duplicate = original.copy()
        self.assertEqual(duplicate.state, "active")
        self.assertNotEqual(duplicate.name, original.name)
        self.assertFalse(duplicate.cancel_reason)

    # --- reservations ---------------------------------------------------------------------

    def test_reservation_has_number_but_no_date(self):
        defaults = self.Ledger.with_context(default_state="reserved").default_get(["record_date"])
        self.assertFalse(defaults.get("record_date"))
        reserved = self.Ledger.create({"record_type": "exit", "state": "reserved"})
        self.assertNotEqual(reserved.name, "New")
        self.assertFalse(reserved.record_date)

    def test_register_reservation_needs_a_date(self):
        reserved = self.Ledger.create({"record_type": "exit", "state": "reserved"})
        with self.assertRaises(UserError):
            reserved.action_confirm()
        reserved.record_date = fields.Date.context_today(reserved)
        reserved.action_confirm()
        self.assertEqual(reserved.state, "active")

    def test_active_record_needs_a_date(self):
        record = self.Ledger.create({"record_type": "entry"})
        with self.assertRaises(ValidationError):
            record.record_date = False

    def test_reservation_date_between_neighbours(self):
        self._record("2097/00001", "2097-02-01")
        reserved = self._record("2097/00002", False, state="reserved")
        self._record("2097/00003", "2097-03-01")
        self.assertEqual(fields.Date.to_string(reserved.date_min), "2097-02-01")
        self.assertEqual(fields.Date.to_string(reserved.date_max), "2097-03-01")
        reserved.record_date = "2097-02-15"
        reserved.record_date = "2097-02-01"  # the bounds themselves are allowed
        with self.assertRaises(ValidationError):
            reserved.record_date = "2097-01-31"
        with self.assertRaises(ValidationError):
            reserved.record_date = "2097-03-02"

    def test_allowed_interval_survives_form_edits(self):
        self._record("2090/00001", "2090-02-01")
        reserved = self._record("2090/00002", False, state="reserved")
        self._record("2090/00003", "2090-03-01")
        with Form(reserved) as form:
            form.record_date = "2090-02-15"
            self.assertEqual(str(form.date_min), "2090-02-01")
            self.assertEqual(str(form.date_max), "2090-03-01")

    def test_reservation_ignores_undated_neighbours(self):
        self._record("2096/00001", "2096-02-01")
        self._record("2096/00002", False, state="reserved")
        reserved = self._record("2096/00003", False, state="reserved")
        self._record("2096/00004", "2096-05-01")
        reserved.record_date = "2096-03-01"

    def test_date_must_be_in_the_year_of_the_number(self):
        reserved = self._record("2095/00001", False, state="reserved")
        with self.assertRaises(ValidationError):
            reserved.record_date = "2096-01-01"

    def test_active_record_cannot_be_dated_before_previous_number(self):
        self._record("2094/00001", "2094-06-01")
        with self.assertRaises(ValidationError):
            self._record("2094/00002", "2094-05-01")

    # --- cancellation -----------------------------------------------------------------------

    def test_cancel_keeps_number_and_reason(self):
        record = self.Ledger.create({"record_type": "entry"})
        name = record.name
        self._cancel(record, reason="Wrong document")
        self.assertEqual(record.state, "canceled")
        self.assertEqual(record.cancel_reason, "Wrong document")
        self.assertEqual(record.name, name)
        self.assertEqual(self.Ledger.search_count([("name", "=", name)]), 1)
        # cancelling again is a no-op
        record.action_cancel(reason="Other")
        self.assertEqual(record.cancel_reason, "Wrong document")

    def test_cancel_reservation(self):
        reserved = self.Ledger.create({"record_type": "exit", "state": "reserved"})
        self._cancel(reserved)
        self.assertEqual(reserved.state, "canceled")
        self.assertFalse(reserved.record_date)

    def test_reactivate_only_for_manager(self):
        dated = self.Ledger.create({"record_type": "entry"})
        undated = self.Ledger.create({"record_type": "entry", "state": "reserved"})
        self._cancel(dated | undated)
        with self.assertRaises(AccessError):
            dated.with_user(self.user).action_reactivate()
        (dated | undated).with_user(self.manager).action_reactivate()
        self.assertEqual(dated.state, "active")
        self.assertEqual(undated.state, "reserved")
        self.assertFalse(dated.cancel_reason)

    # --- access ---------------------------------------------------------------------------------

    def test_only_manager_can_delete(self):
        record = self.Ledger.with_user(self.user).create({"record_type": "entry"})
        with self.assertRaises(AccessError):
            record.unlink()
        record.with_user(self.manager).unlink()
        self.assertFalse(record.exists())

    # --- duplicates, links ---------------------------------------------------------------------

    def test_duplicate_warning(self):
        partner = self.env["res.partner"].create({"name": "Partner"})
        vals = {"record_type": "entry", "document_number": "INV-1", "contact_id": partner.id}
        first = self.Ledger.create(vals)
        second = self.Ledger.create(vals)
        self.assertTrue(second.has_duplicate)
        self._cancel(first)
        second.invalidate_recordset(["has_duplicate"])
        self.assertFalse(second.has_duplicate)

    def test_links(self):
        record = self.Ledger.create({"record_type": "entry"})
        link = self.env["ledger.link"].create(
            {"ledger_id": record.id, "link_type": "url", "url": "https://www.terrabit.ro"}
        )
        self.assertEqual(link.name, "https://www.terrabit.ro")
        with self.assertRaises(ValidationError):
            self.env["ledger.link"].create({"ledger_id": record.id, "link_type": "url"})
        with self.assertRaises(ValidationError):
            self.env["ledger.link"].create({"ledger_id": record.id, "link_type": "record"})
        models = [model for model, _label in self.env["ledger.link"]._selection_reference()]
        if "project.project" in models:
            project = self.env["project.project"].create({"name": "Linked project"})
            link = self.env["ledger.link"].create(
                {"ledger_id": record.id, "link_type": "record", "reference": f"project.project,{project.id}"}
            )
            self.assertEqual(link.name, "Linked project")

    # --- report ---------------------------------------------------------------------------------

    def test_report_wizard(self):
        record = self._record("2093/00001", "2093-04-01")
        reserved = self._record("2093/00002", False, state="reserved")
        wizard = (
            self.env["ledger.report.wizard"]
            .with_context(discard_logo_check=True)
            .create({"date_from": "2093-01-01", "date_to": "2093-12-31"})
        )
        action = wizard.action_print()
        self.assertEqual(action["report_name"], "deltatech_ledger.report_ledger_document")
        self.assertCountEqual(action["context"]["active_ids"], (record | reserved).ids)
        wizard.include_undated = False
        self.assertEqual(wizard.action_print()["context"]["active_ids"], record.ids)
        wizard.date_from = "2092-01-01"
        wizard.date_to = "2092-12-31"
        with self.assertRaises(UserError):
            wizard.action_print()

    def test_report_renders(self):
        record = self._record("2091/00001", "2091-04-01", document_number="X-1")
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(
            "deltatech_ledger.action_report_ledger",
            record.ids,
            data={"date_from": "2091-01-01", "date_to": "2091-12-31"},
        )
        self.assertIn(b"2091/00001", html)
        self.assertIn(b"X-1", html)
