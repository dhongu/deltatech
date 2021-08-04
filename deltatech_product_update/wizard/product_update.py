import base64

from odoo import fields, models

try:
    import xlrd

    try:
        from xlrd import xlsx

    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class ProductImportFile(models.TransientModel):
    _name = "product.import.file"
    _description = "Import product file"

    name = fields.Char(string="File Name")
    data_file = fields.Binary(string="File", required=True)
    vendor_id = fields.Many2one("res.partner", required=True)

    def do_import(self):
        decoded_data = base64.b64decode(self.data_file)
        book = xlrd.open_workbook(file_contents=decoded_data)
        sheet = book.sheet_by_index(0)
        table_values = []
        for row in list(map(sheet.row, range(sheet.nrows))):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(str(cell.value) if is_float else str(int(cell.value)))
                else:
                    values.append(cell.value)
            table_values.append(values)

        for key in table_values:
            product = self.env["product.supplierinfo"].search(
                [("name", "=", self.vendor_id.name), ("product_code", "=", key[0])]
            )
            if product:
                for item in product:
                    item.write({"price": key[1], "min_qty": key[2]})
