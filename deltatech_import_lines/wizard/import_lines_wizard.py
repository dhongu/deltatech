# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import math
import os
import re

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.import_lines_mapping import MATCH_KEYS, TARGETS

ROW_STATUS = [
    ("ok", "OK"),
    ("not_found", "Product not found"),
    ("ambiguous", "Several products"),
    ("invalid_quantity", "Invalid quantity"),
    ("invalid_number", "Invalid number"),
    ("invalid_uom", "Invalid unit of measure"),
    ("lot_error", "Lot/serial error"),
    ("not_allowed", "Not allowed"),
]

FILE_TYPES = {
    ".csv": "text/csv",
    ".txt": "text/csv",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
}

# column titles recognised when the document has no saved mapping (lower case)
HEADER_GUESS = {
    "product": ["product", "produs", "code", "cod", "internal reference", "reference", "ref", "sku", "barcode", "ean"],
    "quantity": ["quantity", "qty", "cantitate", "cant", "cant."],
    "price_unit": ["unit price", "price", "pret", "preț", "pret unitar", "preț unitar"],
    "discount": ["discount", "disc.", "discount (%)", "reducere"],
    "uom": ["uom", "unit", "unit of measure", "um", "u.m.", "unitate de masura", "unitate de măsură"],
    "lot": ["lot", "serial", "lot/serial", "lot/serial number", "serie", "lot/serie"],
    "description": ["description", "descriere", "name", "denumire"],
}


# one comma followed by exactly three digits, as in 1,234: decimal comma or thousands separator
AMBIGUOUS_COMMA = re.compile(r"^-?[1-9]\d{0,2},\d{3}$")


class AmbiguousNumberError(ValueError):
    """A number that reads both as a decimal (1,234 = 1.234) and as an integer (1,234 = 1234)."""


def parse_number(value):
    """Parse a number written with a decimal point or a decimal comma; raise ValueError when invalid."""
    if isinstance(value, bool):
        raise ValueError(value)
    if isinstance(value, int | float):
        return float(value)
    text = str(value or "").strip().replace("\xa0", "").replace(" ", "").replace("'", "").rstrip("%")
    if not text:
        raise ValueError(value)
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        # a single comma is the decimal separator (1,5); several are thousands separators (1,234,567);
        # 1,234 can be either, so it is refused instead of guessed
        if AMBIGUOUS_COMMA.match(text):
            raise AmbiguousNumberError(value)
        text = text.replace(",", ".") if text.count(",") == 1 else text.replace(",", "")
    number = float(text)
    if not math.isfinite(number):
        raise ValueError(value)
    return number


class ImportLinesWizard(models.TransientModel):
    _name = "import.lines.wizard"
    _description = "Import Document Lines"

    res_model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(readonly=True)
    state = fields.Selection(
        [("upload", "File"), ("map", "Columns"), ("preview", "Preview")], default="upload", required=True
    )
    file = fields.Binary(attachment=False)
    file_name = fields.Char()
    partner_id = fields.Many2one("res.partner", readonly=True)
    mapping_id = fields.Many2one(
        "import.lines.mapping", string="Saved Mapping", domain="[('res_model', '=', res_model)]"
    )
    has_header = fields.Boolean("Header Row", default=True)
    separator = fields.Char(help="Column separator for CSV and TXT files. Leave empty to detect it.")
    match_by = fields.Selection(MATCH_KEYS, string="Match Product By", required=True, default="default_code")
    column_ids = fields.One2many("import.lines.wizard.column", "wizard_id", string="Columns")
    row_ids = fields.One2many("import.lines.wizard.row", "wizard_id", string="Rows")
    skip_errors = fields.Boolean("Skip Rows With Errors")
    ok_count = fields.Integer(compute="_compute_counts")
    error_count = fields.Integer(compute="_compute_counts")
    show_price_unit = fields.Boolean(compute="_compute_show_columns")
    show_discount = fields.Boolean(compute="_compute_show_columns")
    show_uom = fields.Boolean(compute="_compute_show_columns")
    show_lot = fields.Boolean(compute="_compute_show_columns")
    show_description = fields.Boolean(compute="_compute_show_columns")
    mapping_name = fields.Char("Mapping Name")
    mapping_for_partner = fields.Boolean("Only For This Partner")

    @api.depends("row_ids.status")
    def _compute_counts(self):
        for wizard in self:
            ok_rows = wizard.row_ids.filtered(lambda r: r.status == "ok")
            wizard.ok_count = len(ok_rows)
            wizard.error_count = len(wizard.row_ids) - len(ok_rows)

    @api.depends("column_ids.target")
    def _compute_show_columns(self):
        for wizard in self:
            targets = set(wizard.column_ids.mapped("target"))
            for target in ("price_unit", "discount", "uom", "lot", "description"):
                wizard[f"show_{target}"] = target in targets

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        context = self.env.context
        # import_lines_model is set for documents without a header record, such as the inventory count
        res_model = context.get("import_lines_model") or context.get("active_model")
        if res_model not in self.env.registry["import.lines.mixin"]._inherit_children:
            raise UserError(self.env._("Lines cannot be imported in this document."))
        res_id = context.get("active_id") if not context.get("import_lines_model") else False
        document = self.env[res_model].browse(res_id or [])
        document._import_lines_check()
        partner = document._import_lines_partner()
        defaults.update({"res_model": res_model, "res_id": document.id, "partner_id": partner.id})
        mapping = self.env["import.lines.mapping"]._find_for(res_model, partner)
        if mapping:
            defaults.update(self._mapping_values(mapping))
        return defaults

    @api.model
    def _mapping_values(self, mapping):
        return {
            "mapping_id": mapping.id,
            "has_header": mapping.has_header,
            "separator": mapping.separator,
            "match_by": mapping.match_by,
        }

    @api.onchange("mapping_id")
    def _onchange_mapping_id(self):
        if self.mapping_id:
            self.update(self._mapping_values(self.mapping_id))

    @api.model
    def _target_label(self, target):
        return dict(self.env["import.lines.wizard.column"]._fields["target"]._description_selection(self.env))[target]

    def _get_document(self):
        self.ensure_one()
        if self.res_model not in self.env.registry["import.lines.mixin"]._inherit_children:
            raise UserError(self.env._("Lines cannot be imported in this document."))
        return self.env[self.res_model].browse(self.res_id or [])

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Import Lines"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": dict(self.env.context, import_lines_model=self.res_model, dialog_size="extra-large"),
        }

    # ------------------------------------------------------------------
    # File
    # ------------------------------------------------------------------
    def _read_file_rows(self):
        """Return the non empty rows of the file as lists of stripped strings."""
        self.ensure_one()
        if not self.file:
            raise UserError(self.env._("Select the file to import."))
        return self._read_rows(base64.b64decode(self.file), self.file_name, self.separator)

    @api.model
    def _read_rows(self, data, file_name, separator=False):
        """Read a spreadsheet or a delimited text file with the readers of the standard import."""
        extension = os.path.splitext(file_name or "")[1].lower()
        reader = self.env["base_import.import"].create(
            {"file": data, "file_name": file_name, "file_type": FILE_TYPES.get(extension, False)}
        )
        options = {"quoting": '"', "separator": separator or "", "encoding": ""}
        try:
            __, rows = reader._read_file(options)
        except UserError:
            raise
        except Exception as error:
            raise UserError(self.env._("The file cannot be read: %s", error)) from error
        reader.unlink()
        return [[str(value).strip() if value is not None else "" for value in row] for row in rows]

    def _split_header(self, rows):
        if self.has_header and rows:
            return rows[0], rows[1:]
        return [], rows

    def action_load(self):
        self.ensure_one()
        rows = self._read_file_rows()
        header, data = self._split_header(rows)
        if not data:
            raise UserError(self.env._("The file has no rows to import."))
        width = max(len(row) for row in rows)
        columns = []
        for index in range(width):
            title = header[index] if index < len(header) else ""
            sample = next((row[index] for row in data if index < len(row) and row[index]), "")
            columns.append(
                {
                    "column_index": index + 1,
                    "header": title,
                    "sample": sample[:100],
                    "target": self._guess_target(index + 1, title, self.mapping_id, self.has_header),
                }
            )
        used = set()
        for column in columns:
            # one column per target, the first one wins
            if column["target"] in used:
                column["target"] = False
            used.add(column["target"])
        self.row_ids.unlink()
        self.write({"column_ids": [(5, 0, 0)] + [(0, 0, vals) for vals in columns], "state": "map"})
        return self._reopen()

    @api.model
    def _guess_target(self, column_index, title, mapping=None, has_header=True):
        """Target of a file column: from the saved mapping, else from the usual column titles."""
        key = (title or "").strip().casefold()
        if mapping:
            if key and has_header:
                column = mapping.column_ids.filtered(lambda c: (c.header or "").strip().casefold() == key)
                if column:
                    return column[0].target
            column = mapping.column_ids.filtered(lambda c: not c.header and c.column_index == column_index)
            return column[0].target if column else False
        if not key:
            return False
        for target, titles in HEADER_GUESS.items():
            if key in titles:
                return target
        return False

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------
    def _mapped_targets(self):
        """Return {target: column index (0 based)} and check the mapping against the document."""
        self.ensure_one()
        mapped = {}
        for column in self.column_ids.filtered("target"):
            if column.target in mapped:
                raise UserError(
                    self.env._(
                        "The %s target is set on more than one column.",
                        self._target_label(column.target),
                    )
                )
            mapped[column.target] = column.column_index - 1
        for target in ("product", "quantity"):
            if target not in mapped:
                raise UserError(self.env._("Map a column to the %s target.", self._target_label(target)))
        document = self._get_document()
        allowed = document._import_lines_targets()
        not_allowed = [self._target_label(target) for target in mapped if target not in allowed]
        if not_allowed:
            raise UserError(self.env._("This document does not use the targets: %s.", ", ".join(not_allowed)))
        if self.match_by not in document._import_lines_match_keys():
            raise UserError(
                self.env._(
                    "Products cannot be matched by %s on this document.",
                    dict(self._fields["match_by"]._description_selection(self.env))[self.match_by],
                )
            )
        return mapped

    def action_save_mapping(self):
        self.ensure_one()
        self._mapped_targets()
        values = {
            "has_header": self.has_header,
            "separator": self.separator,
            "match_by": self.match_by,
            "column_ids": [(5, 0, 0)]
            + [
                (
                    0,
                    0,
                    {
                        "column_index": column.column_index,
                        "header": column.header if self.has_header else False,
                        "target": column.target,
                    },
                )
                for column in self.column_ids.filtered("target")
            ],
        }
        if self.mapping_id and not self.mapping_name:
            self.mapping_id.write(values)
        else:
            partner = self.partner_id.commercial_partner_id if self.mapping_for_partner else False
            values.update(
                {
                    "name": self.mapping_name or self._get_document().display_name or self.res_model,
                    "res_model": self.res_model,
                    "partner_id": partner and partner.id,
                }
            )
            self.mapping_id = self.env["import.lines.mapping"].create(values)
        self.mapping_name = False
        return self._reopen()

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------
    def action_preview(self):
        self.ensure_one()
        mapped = self._mapped_targets()
        __, data = self._split_header(self._read_file_rows())
        first_row = 2 if self.has_header else 1
        document = self._get_document()
        # products and units are looked up once for the whole file, not row by row
        product_index = mapped["product"]
        refs = {values[product_index] for values in data if product_index < len(values) and values[product_index]}
        lookup = {
            "products": document._import_lines_find_products(self.match_by, refs),
            "uoms": {uom.name.casefold(): uom for uom in self.env["uom.uom"].search([])},
        }
        rows = []
        to_check = []
        for row_number, values in enumerate(data, start=first_row):
            row_vals = self._parse_row(document, mapped, values, lookup)
            if row_vals:
                row_vals["row_number"] = row_number
                rows.append(row_vals)
                if row_vals["status"] == "ok":
                    to_check.append(row_vals)
        # the document checks the matched rows together (lots, duplicates)
        row_data = [
            self._row_data(row, self.env["product.product"].browse(row["product_id"]), mapped) for row in to_check
        ]
        for row_vals, error in zip(to_check, document._import_lines_check_rows(row_data), strict=True):
            if error:
                row_vals["status"], row_vals["message"] = error
        if not rows:
            raise UserError(self.env._("The file has no rows with a product."))
        self.write({"row_ids": [(5, 0, 0)] + [(0, 0, vals) for vals in rows], "state": "preview"})
        return self._reopen()

    def _parse_row(self, document, mapped, values, lookup):
        def cell(target):
            index = mapped.get(target)
            if index is None or index >= len(values):
                return ""
            return values[index]

        product_ref = cell("product")
        quantity_text = cell("quantity")
        if not product_ref:
            # blank or total row
            return False
        row = {
            "product_ref": product_ref,
            "uom_name": cell("uom"),
            "lot_name": cell("lot"),
            "description": cell("description"),
            "status": "ok",
        }
        errors = []
        try:
            row["quantity"] = parse_number(quantity_text)
            if row["quantity"] < 0 or (not row["quantity"] and not document._import_lines_allow_zero_quantity()):
                errors.append(("invalid_quantity", quantity_text))
        except ValueError as error:
            errors.append(("invalid_quantity", self._number_error(quantity_text, error)))
        for target in ("price_unit", "discount"):
            if target in mapped and cell(target):
                try:
                    row[target] = parse_number(cell(target))
                    row[f"has_{target}"] = True
                except ValueError as error:
                    errors.append(
                        ("invalid_number", f"{self._target_label(target)}: {self._number_error(cell(target), error)}")
                    )

        products = lookup["products"].get(product_ref, self.env["product.product"])
        if not products:
            errors.append(("not_found", product_ref))
        elif len(products) > 1:
            errors.append(("ambiguous", ", ".join(products.mapped("display_name"))))
        else:
            row["product_id"] = products.id
            if row["uom_name"]:
                uom = lookup["uoms"].get(row["uom_name"].casefold())
                if not uom or not uom._has_common_reference(products.uom_id):
                    errors.append(("invalid_uom", row["uom_name"]))
                else:
                    row["uom_id"] = uom.id
        if errors:
            row["status"] = errors[0][0]
            row["message"] = "; ".join(str(message) for __, message in errors if message)
        return row

    def _number_error(self, text, error):
        if isinstance(error, AmbiguousNumberError):
            return self.env._(
                "%s is ambiguous (decimal comma or thousands separator): remove the comma for an integer "
                "or use a decimal point for a decimal number",
                text,
            )
        return text

    def _row_data(self, row, product, mapped):
        """Values handed to the document adapter; only the mapped optional targets are present."""
        uom = self.env["uom.uom"].browse(row.get("uom_id"))
        data = {"product": product, "quantity": row.get("quantity", 0.0), "uom": uom}
        for target, key in (("price_unit", "price_unit"), ("discount", "discount")):
            if target in mapped and key in row:
                data[key] = row[key]
        if "lot" in mapped:
            data["lot_name"] = row.get("lot_name") or ""
        if "description" in mapped and row.get("description"):
            data["description"] = row["description"]
        return data

    def action_back(self):
        self.ensure_one()
        self.write({"row_ids": [(5, 0, 0)], "state": "map"})
        return self._reopen()

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------
    def action_import(self):
        self.ensure_one()
        if self.error_count and not self.skip_errors:
            raise UserError(
                self.env._(
                    "%(count)s rows have errors. Fix the file or tick Skip Rows With Errors.",
                    count=self.error_count,
                )
            )
        mapped = self._mapped_targets()
        document = self._get_document()
        document._import_lines_check()
        rows = [self._row_data(row._row_values(), row.product_id, mapped) for row in self.row_ids if row.status == "ok"]
        if not rows:
            raise UserError(self.env._("There are no valid rows to import."))
        document._import_lines_create(rows, self)
        return {"type": "ir.actions.act_window_close"}


class ImportLinesWizardColumn(models.TransientModel):
    _name = "import.lines.wizard.column"
    _description = "Import Lines Wizard Column"
    _order = "column_index"

    wizard_id = fields.Many2one("import.lines.wizard", required=True, ondelete="cascade")
    column_index = fields.Integer("Column", readonly=True)
    header = fields.Char("Title", readonly=True)
    sample = fields.Char("First Value", readonly=True)
    target = fields.Selection(TARGETS, string="Import As")


class ImportLinesWizardRow(models.TransientModel):
    _name = "import.lines.wizard.row"
    _description = "Import Lines Wizard Row"
    _order = "row_number"

    wizard_id = fields.Many2one("import.lines.wizard", required=True, ondelete="cascade")
    row_number = fields.Integer("Row")
    product_ref = fields.Char("File Product")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(digits="Product Unit")
    uom_name = fields.Char("File Unit")
    uom_id = fields.Many2one("uom.uom", string="Unit")
    price_unit = fields.Float("Unit Price", digits="Product Price")
    has_price_unit = fields.Boolean()
    discount = fields.Float("Discount (%)", digits="Discount")
    has_discount = fields.Boolean()
    lot_name = fields.Char("Lot/Serial Number")
    description = fields.Char()
    status = fields.Selection(ROW_STATUS, required=True, default="ok")
    message = fields.Char()

    def _row_values(self):
        """Parsed values of the row, without the price and discount left empty in the file."""
        self.ensure_one()
        values = {
            "quantity": self.quantity,
            "uom_id": self.uom_id.id,
            "lot_name": self.lot_name,
            "description": self.description,
        }
        if self.has_price_unit:
            values["price_unit"] = self.price_unit
        if self.has_discount:
            values["discount"] = self.discount
        return values
