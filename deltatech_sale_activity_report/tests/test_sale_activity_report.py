# Copyright (C) 2025 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses.html#odoo-apps).
import base64
import io
from datetime import date

from PIL import Image

from odoo.tests import TransactionCase, tagged

from odoo.addons.deltatech_sale_activity_report.models.sale_order import (
    MAX_LOG_LENGTH,
    MAX_VALUE_LENGTH,
    format_line_ref,
)


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

    def _binary_payload(self):
        """Conținut binar valid pentru un câmp de tip imagine (semnătura)."""
        buffer = io.BytesIO()
        Image.new("RGB", (400, 400), "#123456").save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue())

    def test_binary_field_is_not_logged(self):
        """Câmpurile binare (semnătură, etichetă AWB) nu ajung în jurnal.

        Serializarea lor scria în ``activity_log`` conținutul base64 al
        fișierului — sute de kB per scriere, ajunși în baza clientului.
        """
        payload = self._binary_payload()

        self.order.with_user(self.salesman).write({"signature": payload})

        log = self._records().activity_log or ""
        self.assertNotIn(payload.decode()[:50], log)
        self.assertLess(len(log), 1000)

    def test_binary_field_skipped_but_others_logged(self):
        """Un binar scris împreună cu alte câmpuri nu contaminează jurnalul."""
        payload = self._binary_payload()

        self.order.with_user(self.salesman).write({"client_order_ref": "PO-BIN", "signature": payload})

        records = self._records()
        self.assertEqual(len(records), 1)
        self.assertIn("PO-BIN", records.activity_log)
        self.assertNotIn(payload.decode()[:50], records.activity_log)
        self.assertLess(len(records.activity_log), 1000)

    def test_long_value_is_truncated(self):
        """Valorile text lungi sunt scurtate, cu marcarea restului tăiat."""
        self.order.with_user(self.salesman).write({"client_order_ref": "A" * 5000})

        log = self._records().activity_log
        self.assertIn("A" * MAX_VALUE_LENGTH, log)
        self.assertNotIn("A" * (MAX_VALUE_LENGTH + 1), log)
        self.assertIn("chars)", log)

    def test_virtual_line_id_is_not_read_from_db(self):
        """Id-ul virtual al unei linii nesalvate nu mai e citit din baza de date.

        Clientul web trimite comenzi x2many care pot referi o linie încă
        nesalvată prin id-ul ei virtual (``[2, "virtual_7149"]``). Un ``browse``
        pe un astfel de id producea un recordset cu un id per caracter, iar
        citirea numelui arunca ``Expected singleton`` — se pierdea jurnalul
        întregii scrieri.
        """
        lines = self.env["sale.order.line"]

        self.assertEqual(format_line_ref(lines, "virtual_7149"), "ID virtual_7149")
        # Un id inexistent (linie ștearsă între timp) nu trebuie nici el să arunce.
        self.assertEqual(format_line_ref(lines, 999999999), "ID 999999999")

        line = self.order.order_line
        self.assertEqual(format_line_ref(lines, line.id), line.display_name)

    def test_activity_log_is_capped(self):
        """Jurnalul unei zile nu depășește plafonul, păstrând activitatea recentă."""
        order = self.order.with_user(self.salesman)
        order.write({"client_order_ref": "FIRST"})

        record = self._records()
        record.sudo().activity_log = "old line\n" * (MAX_LOG_LENGTH // 9)

        order.write({"client_order_ref": "LAST"})

        log = self._records().activity_log
        self.assertLessEqual(len(log), MAX_LOG_LENGTH)
        self.assertIn("LAST", log)

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
