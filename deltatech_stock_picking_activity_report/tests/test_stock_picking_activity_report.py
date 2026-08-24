# Copyright (C) 2025 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses.html#odoo-apps).
import base64
import io
from datetime import date

from PIL import Image

from odoo.tests import TransactionCase, tagged

from odoo.addons.deltatech_stock_picking_activity_report.models.stock_picking import (
    MAX_LOG_LENGTH,
    MAX_VALUE_LENGTH,
    format_record_ref,
)


@tagged("post_install", "-at_install")
class TestStockPickingActivityReport(TransactionCase):
    """Tests for the stock.picking activity logging introduced by
    deltatech_stock_picking_activity_report.

    As with the sale variant, logging only fires for a real internal user
    whose login is not ``__system__``. The default test env is OdooBot, so
    operations that should log are run through ``self.stock_user``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Record = cls.env["stock.picking.activity.record"]

        cls.stock_user = cls.env["res.users"].create(
            {
                "name": "Activity Stock User",
                "login": "activity_stock_user",
                "email": "activity_stock_user@example.com",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("stock.group_stock_user").id,
                        ],
                    )
                ],
            }
        )
        # Dacă în aceeași bază e instalat și deltatech_picking_restrict_entry_exit
        # (cazul CI pe tot repo-ul), userul de test trebuie scutit de restricția
        # care cere linie de vânzare/achiziție la validare — aceste teste verifică
        # doar logarea activității, pe picking-uri de sine stătătoare. Nu adăugăm
        # dependență în manifest; referința e opțională.
        restrict_group = cls.env.ref(
            "deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit",
            raise_if_not_found=False,
        )
        if restrict_group:
            cls.stock_user.group_ids = [(4, restrict_group.id)]

        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.picking_type_out = cls.warehouse.out_type_id

        cls.product = cls.env["product.product"].create(
            {
                "name": "Activity Storable",
                "is_storable": True,
            }
        )

    def _new_picking(self, qty=3.0):
        """Create a draft outgoing picking with one move."""
        return self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )

    def _binary_payload(self):
        """Conținut binar valid pentru un câmp de tip imagine (semnătura)."""
        buffer = io.BytesIO()
        Image.new("RGB", (400, 400), "#123456").save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue())

    def _records(self, picking):
        return self.Record.search([("picking_id", "=", picking.id), ("user_id", "=", self.stock_user.id)])

    def test_create_does_not_log(self):
        picking = self._new_picking()
        self.assertFalse(
            self._records(picking),
            "No activity record should exist right after picking creation.",
        )

    def test_write_creates_record_with_log(self):
        picking = self._new_picking().with_user(self.stock_user)
        picking.write({"origin": "SRC-001"})

        records = self._records(picking)
        self.assertEqual(len(records), 1)
        self.assertEqual(records.change_date, date.today())
        self.assertEqual(records.user_id, self.stock_user)
        self.assertEqual(records.state, picking.state)
        self.assertIn("SRC-001", records.activity_log)

    def test_write_same_day_appends_to_single_record(self):
        picking = self._new_picking().with_user(self.stock_user)
        picking.write({"origin": "SRC-001"})
        picking.write({"origin": "SRC-002"})

        records = self._records(picking)
        self.assertEqual(len(records), 1, "Same-day writes must not duplicate records.")
        log = records.activity_log
        self.assertIn("SRC-001", log)
        self.assertIn("SRC-002", log)
        self.assertEqual(
            len([line for line in log.splitlines() if line.strip()]),
            2,
        )

    def test_binary_field_is_not_logged(self):
        """Câmpurile binare (semnătură, etichetă AWB) nu ajung în jurnal.

        Serializarea lor scria în ``activity_log`` conținutul base64 al
        fișierului — sute de kB per scriere, ajunși în baza clientului.
        """
        picking = self._new_picking().with_user(self.stock_user)
        payload = self._binary_payload()

        picking.write({"signature": payload})

        # Semnarea postează un mesaj în chatter ("Order signed"), deci o
        # înregistrare tot apare — dar fără urmă din conținutul binar.
        log = self._records(picking).activity_log or ""
        self.assertNotIn(payload.decode()[:50], log)
        self.assertLess(len(log), 1000)

    def test_binary_field_skipped_but_others_logged(self):
        """Un binar scris împreună cu alte câmpuri nu contaminează jurnalul."""
        picking = self._new_picking().with_user(self.stock_user)
        payload = self._binary_payload()

        picking.write({"origin": "SRC-BIN", "signature": payload})

        records = self._records(picking)
        self.assertEqual(len(records), 1)
        self.assertIn("SRC-BIN", records.activity_log)
        self.assertNotIn(payload.decode()[:50], records.activity_log)
        self.assertLess(len(records.activity_log), 1000)

    def test_virtual_line_id_is_not_read_from_db(self):
        """Id-ul virtual al unei operații nesalvate nu mai e citit din baza de date.

        Clientul web referă liniile încă nesalvate prin id-uri virtuale
        (``[2, "virtual_7149"]``). Un ``browse`` pe un astfel de id producea un
        recordset cu un id per caracter, iar citirea numelui arunca
        ``Expected singleton`` — se pierdea jurnalul întregii scrieri.
        """
        moves = self.env["stock.move"]
        move = self._new_picking().move_ids

        self.assertEqual(format_record_ref(moves, "virtual_7149"), "ID virtual_7149")
        # Un id inexistent (linie ștearsă între timp) nu trebuie nici el să arunce.
        self.assertEqual(format_record_ref(moves, 999999999), "ID 999999999")
        # Id real, recordset și câmp fără relație cunoscută.
        self.assertEqual(format_record_ref(moves, move.id), move.display_name)
        self.assertEqual(format_record_ref(moves, move), move.display_name)
        self.assertEqual(format_record_ref(None, "virtual_1"), "ID virtual_1")

    def test_move_commands_are_described_by_name(self):
        """Comenzile pe operații sunt descrise cu numele liniei, nu cu id-ul brut."""
        picking = self._new_picking().with_user(self.stock_user)
        move = picking.move_ids
        # Numele se citește înainte de ștergere: după (2, id) operația nu mai există.
        move_name = move.display_name

        picking.write({"move_ids": [(1, move.id, {"product_uom_qty": 9})]})
        log = self._records(picking).activity_log
        self.assertIn(f"Update {move_name}", log)
        self.assertIn("9", log)

        picking.write(
            {
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ]
            }
        )
        self.assertIn(f"Add New ({self.product.display_name})", self._records(picking).activity_log)

        other_move = self._new_picking(qty=1).move_ids
        other_name = other_move.display_name
        picking.write({"move_ids": [(4, other_move.id)]})
        self.assertIn(f"Link {other_name}", self._records(picking).activity_log)

        picking.write({"move_ids": [(3, other_move.id)]})
        self.assertIn(f"Remove {other_name}", self._records(picking).activity_log)

        # Ștergerea unei mișcări de stoc e rezervată managerului de stoc; testul
        # verifică descrierea comenzii, deci ridicăm dreptul doar aici.
        self.stock_user.group_ids = [(4, self.env.ref("stock.group_stock_manager").id)]
        picking.write({"move_ids": [(2, move.id)]})
        self.assertIn(f"Delete {move_name}", self._records(picking).activity_log)

    def test_many2one_change_is_logged_with_display_name(self):
        """Un many2one e jurnalizat cu numele înregistrării, nu cu id-ul."""
        picking = self._new_picking().with_user(self.stock_user)
        partner = self.env["res.partner"].create({"name": "Destinatar activitate"})

        picking.write({"partner_id": partner.id})

        log = self._records(picking).activity_log
        self.assertIn(partner.display_name, log)
        self.assertNotIn(f"ID {partner.id}", log)

    def test_long_value_is_truncated(self):
        """Valorile text lungi sunt scurtate, cu marcarea restului tăiat."""
        picking = self._new_picking().with_user(self.stock_user)

        picking.write({"origin": "A" * 5000})

        log = self._records(picking).activity_log
        self.assertIn("A" * MAX_VALUE_LENGTH, log)
        self.assertNotIn("A" * (MAX_VALUE_LENGTH + 1), log)
        self.assertIn("chars)", log)

    def test_activity_log_is_capped(self):
        """Jurnalul unei zile nu depășește plafonul, păstrând activitatea recentă."""
        picking = self._new_picking().with_user(self.stock_user)
        picking.write({"origin": "FIRST"})

        record = self._records(picking)
        record.sudo().activity_log = "old line\n" * (MAX_LOG_LENGTH // 9)

        picking.write({"origin": "LAST"})

        log = self._records(picking).activity_log
        self.assertLessEqual(len(log), MAX_LOG_LENGTH)
        self.assertIn("LAST", log)

    def test_action_confirm_logs_button(self):
        picking = self._new_picking().with_user(self.stock_user)
        picking.action_confirm()

        records = self._records(picking)
        self.assertEqual(len(records), 1)
        self.assertIn("Button Clicked: Confirm", records.activity_log)

    def test_message_post_logs_and_flags_chatter(self):
        picking = self._new_picking().with_user(self.stock_user)
        picking.message_post(body="<p>Picking <b>note</b></p>")

        records = self._records(picking)
        self.assertEqual(len(records), 1)
        self.assertTrue(records.chatter_message)
        self.assertIn("Message: Picking note", records.activity_log)

    def test_system_user_does_not_log(self):
        self.assertEqual(self.env.user.login, "__system__")
        picking = self._new_picking()
        picking.write({"origin": "SYS"})
        self.assertFalse(
            self.Record.search([("picking_id", "=", picking.id)]),
            "System user activity must not be recorded.",
        )

    def test_button_validate_outgoing_sets_exit_number(self):
        """Validating an outgoing picking flags it validated and records the
        exit product count end-to-end."""
        qty = 4.0
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, qty)

        picking = self._new_picking(qty=qty).with_user(self.stock_user)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = qty
            move.picked = True

        result = picking.button_validate()
        self.assertIs(result, True, "Picking should validate directly without a wizard.")
        self.assertEqual(picking.state, "done")

        records = self._records(picking)
        self.assertTrue(records, "Validation should have produced a record.")
        self.assertTrue(records.has_validated)
        self.assertEqual(records.has_validated_count, 1)
        self.assertEqual(records.exit_product_number, qty)
        self.assertIn("Button Clicked: Validate", records.activity_log)

    def test_log_helper_maps_context_fields(self):
        """The logging helper maps incoming/awb context keys onto the record,
        covering the entry/awb branches without a full stock validation."""
        picking = self._new_picking()
        picking.with_user(self.stock_user).with_context(
            entry_product_number=7.0,
            awb_generated=True,
            has_validated=True,
        )._log_picking_activity_report("Button Clicked: Validate")

        records = self._records(picking)
        self.assertEqual(len(records), 1)
        self.assertEqual(records.entry_product_number, 7.0)
        self.assertTrue(records.awb_generated)
        self.assertTrue(records.has_validated)
        self.assertEqual(records.has_validated_count, 1)

    def test_compute_counts_on_record(self):
        """The stored count fields mirror their boolean flags."""
        rec = self.Record.create(
            {
                "picking_id": self._new_picking().id,
                "user_id": self.stock_user.id,
                "has_validated": True,
                "chatter_message": True,
            }
        )
        self.assertEqual(rec.has_validated_count, 1)
        self.assertEqual(rec.chatter_message_count, 1)

        rec.write({"has_validated": False, "chatter_message": False})
        self.assertEqual(rec.has_validated_count, 0)
        self.assertEqual(rec.chatter_message_count, 0)
