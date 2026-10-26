# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.deltatech_import_lines.tests.common import ImportLinesCommon


@tagged("post_install", "-at_install")
class TestImportLinesMrp(ImportLinesCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.finished = cls.env["product.product"].create(
            {"name": "Import Cabinet", "default_code": "IL-CAB", "is_storable": True}
        )
        cls.board = cls.env["product.product"].create(
            {"name": "Import Board", "default_code": "IL-BRD", "is_storable": True}
        )
        cls.hinge = cls.env["product.product"].create(
            {"name": "Import Hinge", "default_code": "IL-HNG", "is_storable": True}
        )

    def _production(self):
        form = Form(self.env["mrp.production"])
        form.product_id = self.finished
        form.product_qty = 2
        return form.save()

    def test_import_components_draft_and_confirmed(self):
        production = self._production()
        rows = [["Code", "Qty"], ["IL-BRD", "4"], ["IL-CAB", "1"]]
        wizard = self._open_wizard(production, rows)
        wizard.action_preview()
        self.assertEqual(wizard.row_ids.mapped("status"), ["ok", "not_allowed"])
        wizard.skip_errors = True
        wizard.action_import()
        self.assertRecordValues(production.move_raw_ids, [{"product_id": self.board.id, "product_uom_qty": 4.0}])

        production.action_confirm()
        wizard = self._open_wizard(production, [["Code", "Qty"], ["IL-HNG", "8"]])
        wizard.action_preview()
        wizard.action_import()
        hinge_move = production.move_raw_ids.filtered(lambda m: m.product_id == self.hinge)
        self.assertEqual(hinge_move.product_uom_qty, 8.0)
        self.assertEqual(hinge_move.state, "confirmed")

    def test_price_not_used(self):
        production = self._production()
        wizard = self._open_wizard(production, [["Code", "Qty", "Price"], ["IL-BRD", "1", "5"]])
        with self.assertRaises(UserError):
            wizard.action_preview()
