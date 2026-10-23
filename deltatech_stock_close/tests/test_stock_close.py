# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from datetime import date, datetime

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase
from odoo.tools import SQL


@tagged("post_install", "-at_install")
class TestStockClose(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tz="UTC"))
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.product = cls.env["product.product"].create(
            {"name": "TEST Stock Close", "type": "consu", "is_storable": True, "standard_price": 10.0}
        )
        cls.account = cls.env["account.account"].search(
            [("company_ids", "in", cls.company.ids), ("account_type", "=", "asset_current")], limit=1
        )
        cls.move_old = cls._receive(5.0, datetime(2025, 12, 31, 12, 0))
        cls.move_new = cls._receive(3.0, datetime(2026, 1, 15, 12, 0))

    @classmethod
    def _receive(cls, qty, move_date):
        move = cls.env["stock.move"].create(
            {
                "product_id": cls.product.id,
                "product_uom_qty": qty,
                "location_id": cls.supplier_location.id,
                "location_dest_id": cls.location.id,
                "company_id": cls.company.id,
            }
        )
        move._action_confirm()
        move.quantity = qty
        move.picked = True
        move._action_done()
        # write the pending ORM values (date, state...) first: flushed after the raw UPDATE,
        # they would overwrite the backdated date
        cls.env.flush_all()
        # the storage sheet only reads moves with a Romanian valuation account
        cls.env.cr.execute(
            SQL(
                "UPDATE stock_move SET date = %s, l10n_ro_account_id = %s WHERE id = %s",
                move_date,
                cls.account.id,
                move.id,
            )
        )
        move.invalidate_recordset()
        return move

    def _close_until(self, close_date):
        wizard = Form(self.env["stock.close.moves"])
        wizard.date = close_date
        return wizard.save().action_close()

    def _storage_sheet_in_qty(self, only_active):
        sheet = self.env["l10n.ro.stock.storage.sheet"].create(
            {
                "location_id": self.location.id,
                "product_ids": [(6, 0, self.product.ids)],
                "date_from": date(2025, 12, 1),
                "date_to": date(2026, 1, 31),
                "only_active": only_active,
            }
        )
        sheet.do_compute_product()
        lines = self.env["l10n.ro.stock.storage.sheet.line"].search([("report_id", "=", sheet.id)])
        return sum(lines.mapped("quantity_in"))

    def test_close_moves_until_date(self):
        self._close_until(date(2025, 12, 31))
        self.assertFalse(self.move_old.l10n_ro_valuation_active)
        self.assertTrue(self.move_new.l10n_ro_valuation_active)

    def test_storage_sheet_only_active_leaves_closed_moves_out(self):
        self.assertEqual(self._storage_sheet_in_qty(only_active=True), 8.0)
        self._close_until(date(2025, 12, 31))
        self.assertEqual(self._storage_sheet_in_qty(only_active=True), 3.0)
        self.assertEqual(self._storage_sheet_in_qty(only_active=False), 8.0)

    def test_valuation_active_shown_in_move_list(self):
        arch = self.env["stock.move"].get_view(self.env.ref("stock.view_move_tree").id, "list")["arch"]
        arch = arch.decode() if isinstance(arch, bytes) else arch
        self.assertIn('name="l10n_ro_valuation_active"', arch)
