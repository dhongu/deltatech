# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64

from odoo.tests import tagged

from ..wizard.import_lines_wizard import parse_number
from .common import ImportLinesCommon


@tagged("post_install", "-at_install")
class TestImportLines(ImportLinesCommon):
    def test_parse_number(self):
        self.assertEqual(parse_number("12"), 12.0)
        self.assertEqual(parse_number("1,5"), 1.5)
        self.assertEqual(parse_number("1.234,56"), 1234.56)
        self.assertEqual(parse_number("1,234.56"), 1234.56)
        self.assertEqual(parse_number("1 234,5"), 1234.5)
        self.assertEqual(parse_number("10%"), 10.0)
        self.assertEqual(parse_number(3), 3.0)
        for value in ("", "abc", True):
            with self.assertRaises(ValueError):
                parse_number(value)

    def _read(self, rows, file_type, **vals):
        data = base64.b64decode(self._file(rows, file_type, **vals))
        return self.env["import.lines.wizard"]._read_rows(data, f"lines.{file_type}")

    def test_read_csv_and_txt(self):
        rows = [["Code", "Qty"], ["A1", "2,5"], ["", ""], ["B2", "3"]]
        self.assertEqual(self._read(rows, "csv"), [["Code", "Qty"], ["A1", "2,5"], ["B2", "3"]])
        self.assertEqual(self._read(rows, "txt", separator="\t"), [["Code", "Qty"], ["A1", "2,5"], ["B2", "3"]])

    def test_read_xlsx(self):
        rows = [["Code", "Qty", "Price"], ["A1", 2, 10.5]]
        self.assertEqual(self._read(rows, "xlsx"), [["Code", "Qty", "Price"], ["A1", "2", "10.5"]])

    def test_guess_target(self):
        wizard = self.env["import.lines.wizard"]
        self.assertEqual(wizard._guess_target(1, "Cantitate"), "quantity")
        self.assertEqual(wizard._guess_target(2, " SKU "), "product")
        self.assertEqual(wizard._guess_target(3, "Preț unitar"), "price_unit")
        self.assertFalse(wizard._guess_target(4, "Observații"))
