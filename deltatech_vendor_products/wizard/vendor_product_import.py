import base64
import logging

from odoo import fields, models

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


_logger = logging.getLogger(__name__)


class VendorProductImport(models.TransientModel):
    _name = "vendor.product.import"
    _description = "Import vendor products"

    data_file = fields.Binary(string="File")
    filename = fields.Char("File Name")
    supplier_id = fields.Many2one("res.partner", string="Supplier", index=True)

    fields_list = fields.Char(string="Fields", default="code,name,list_price,purchase_price,barcode")

    state = fields.Selection([("choose", "choose"), ("view", "view")], default="choose")

    def do_import(self):
        if self.state == "choose":
            decoded_data = base64.b64decode(self.data_file)
            return self.do_import_from_file(decoded_data)

    def do_import_from_file(self, file_contents):
        book = xlrd.open_workbook(file_contents=file_contents)
        sheet = book.sheet_by_index(0)
        table_values = []
        _logger.info("Importing %s rows from %s", sheet.nrows, self.filename)
        for row in list(map(sheet.row, range(sheet.nrows))):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(str(cell.value) if is_float else str(int(cell.value)))
                else:
                    values.append(cell.value)
            values.append(self.supplier_id.id)
            table_values.append(values)
            if len(table_values) > 5000:
                self._process_table_values(table_values)
                table_values = []

        if not table_values:
            return
        self._process_table_values(table_values)
        _logger.info("Imported %s rows from %s", sheet.nrows, self.filename)

    def _process_table_values(self, table_values):
        table_values.pop(0)
        fields_list = self.fields_list.split(",") + ["supplier_id"]
        self.env["vendor.product"]._load_data_in_table(table_values, fields_list)
