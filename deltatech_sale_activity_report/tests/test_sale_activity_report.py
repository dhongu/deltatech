# Copyright (C) 2025 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses.html#odoo-apps).
from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleActivityReport(TransactionCase):
    """Tests for the sale.order activity logging introduced by
    deltatech_sale_activity_report.

    The logging only fires for a real internal user whose login is not
    ``__system__``. The default test environment runs as OdooBot
    (``__system__``), so every operation that should produce a log is run
    through ``self.salesman`` via ``with_user``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Record = cls.env["sale.order.activity.record"]

        # A real internal salesperson (login != "__system__") so the logging
        # guard in the module is satisfied.
        cls.salesman = cls.env["res.users"].create(
            {
                "name": "Activity Salesperson",
                "login": "activity_salesperson",
                "email": "activity_salesperson@example.com",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("sales_team.group_sale_salesman").id,
                        ],
                    )
                ],
            }
        )

        cls.partner = cls.env["res.partner"].create({"name": "Activity Customer"})
        # A service product so confirming the order never launches a stock
        # rule. Otherwise, when mrp/sale_stock are installed (as on CI),
        # action_confirm runs procurement which calls mrp.bom._bom_find, and the
        # salesman (no Inventory/Manufacturing rights) hits an AccessError on
        # mrp.bom -- unrelated to what this suite actually tests.
        cls.product = cls.env["product.product"].create(
            {"name": "Activity Product", "list_price": 100.0, "type": "service"}
        )

        # Created as the salesperson; create() is not overridden, so this does
        # not by itself produce an activity record.
        cls.order = (
            cls.env["sale.order"]
            .with_user(cls.salesman)
            .create(
                {
                    "partner_id": cls.partner.id,
                    "order_line": [
                        (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1}),
                    ],
                }
            )
        )

    def _records(self, order=None):
        order = order or self.order
        return self.Record.search([("sale_order_id", "=", order.id), ("user_id", "=", self.salesman.id)])

    def test_create_does_not_log(self):
        """Creating an order must not create an activity record on its own."""
        self.assertFalse(
            self._records(),
            "No activity record should exist right after order creation.",
        )

    def test_write_creates_record_with_log(self):
        """A write by a salesperson creates one dated record and logs the change."""
        self.order.with_user(self.salesman).write({"client_order_ref": "PO-001"})

        records = self._records()
        self.assertEqual(len(records), 1, "Exactly one activity record expected.")
        rec = records
        self.assertEqual(rec.change_date, date.today())
        self.assertEqual(rec.user_id, self.salesman)
        self.assertEqual(rec.state, self.order.state)
        self.assertIn("Customer Reference", rec.activity_log)
        self.assertIn("PO-001", rec.activity_log)

    def test_write_same_day_appends_to_single_record(self):
        """Multiple writes the same day by the same user reuse one record and
        accumulate log lines instead of creating duplicates."""
        order = self.order.with_user(self.salesman)
        order.write({"client_order_ref": "PO-001"})
        order.write({"client_order_ref": "PO-002"})

        records = self._records()
        self.assertEqual(len(records), 1, "Same-day writes must not duplicate records.")
        log = records.activity_log
        self.assertIn("PO-001", log)
        self.assertIn("PO-002", log)
        # Two changes -> two timestamped log lines.
        self.assertEqual(
            len([line for line in log.splitlines() if line.strip()]),
            2,
            "Each logged change should add one line.",
        )

    def test_no_log_for_unchanged_write(self):
        """Writing the same value produces no change and therefore no record."""
        self.order.with_user(self.salesman).write({"client_order_ref": False})
        self.assertFalse(
            self._records(),
            "Writing an unchanged value should not create a record.",
        )

    def test_action_confirm_logs_button(self):
        """action_confirm appends a 'Button Clicked: Confirm' entry."""
        self.order.with_user(self.salesman).action_confirm()

        records = self._records()
        self.assertEqual(len(records), 1)
        self.assertIn("Button Clicked: Confirm", records.activity_log)
        # State on the record reflects the confirmed order.
        self.assertEqual(records.state, "sale")

    def test_message_post_logs_and_flags_chatter(self):
        """Posting a chatter message logs the (HTML-stripped) body and sets the
        chatter_message flag."""
        self.order.with_user(self.salesman).message_post(body="<p>Hello <b>world</b></p>")

        records = self._records()
        self.assertEqual(len(records), 1)
        self.assertTrue(records.chatter_message)
        self.assertIn("Message: Hello world", records.activity_log)

    def test_system_user_does_not_log(self):
        """Operations performed as OdooBot (__system__) must not be logged."""
        # self.env runs as OdooBot in tests; build the order in this env too so
        # the write is genuinely performed by the system user.
        self.assertEqual(self.env.user.login, "__system__")
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 1}),
                ],
            }
        )
        order.write({"client_order_ref": "SYS"})
        self.assertFalse(
            self.Record.search([("sale_order_id", "=", order.id)]),
            "System user activity must not be recorded.",
        )

    def test_mail_activity_create_logs(self):
        """Scheduling a mail.activity on the order records an activity entry.

        The module reads ``sale.order.stage`` here, a field contributed by
        deltatech_website_sale_status. Skip when that field is absent.
        """
        if "stage" not in self.env["sale.order"]._fields:
            self.skipTest("sale.order.stage not present (deltatech_website_sale_status)")

        activity_type = self.env.ref("mail.mail_activity_data_todo")
        self.env["mail.activity"].with_user(self.salesman).create(
            {
                "activity_type_id": activity_type.id,
                "res_model_id": self.env["ir.model"]._get("sale.order").id,
                "res_id": self.order.id,
                "summary": "Follow up",
            }
        )

        records = self._records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records.state, self.order.state)
