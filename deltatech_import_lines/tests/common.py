# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import io

import openpyxl

from odoo.tests.common import TransactionCase


class ImportLinesCommon(TransactionCase):
    """Helpers to build a file and run the import lines wizard on a document."""

    @classmethod
    def _file(cls, rows, file_type="csv", separator=";"):
        if file_type == "xlsx":
            book = openpyxl.Workbook()
            for row in rows:
                book.active.append(row)
            buffer = io.BytesIO()
            book.save(buffer)
            data = buffer.getvalue()
        else:
            data = "\n".join(separator.join(str(value) for value in row) for row in rows).encode()
        return base64.b64encode(data)

    def _open_wizard(self, document, rows, file_type="csv", context=None, **vals):
        """Create the wizard for ``document`` with a file of ``rows`` and load its columns."""
        ctx = {"active_model": document._name, "active_id": document.id}
        ctx.update(context or {})
        values = {"file": self._file(rows, file_type), "file_name": f"lines.{file_type}"}
        values.update(vals)
        wizard = self.env["import.lines.wizard"].with_context(**ctx).create(values)
        wizard.action_load()
        return wizard

    def _set_targets(self, wizard, targets):
        """Map the columns: ``targets`` is {column position (from 1): target}."""
        for column in wizard.column_ids:
            column.target = targets.get(column.column_index, False)
