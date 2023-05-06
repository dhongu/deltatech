# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import logging

import requests

from odoo import api, fields, models

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

    url = fields.Char(string="URL")
    data_file = fields.Binary(string="File")
    filename = fields.Char("File Name")
    supplier_id = fields.Many2one("res.partner", string="Supplier")
    vendor_info_id = fields.Many2one("vendor.info", string="Vendor Info", ondelete="cascade")
    fields_list = fields.Char(string="Fields", default="code,name,list_price,purchase_price,barcode")
    source_type = fields.Selection([("file", "File"), ("url", "URL")], default="file", required=True, string="Source")

    state = fields.Selection([("choose", "choose"), ("view", "view")], default="choose")

    @api.onchange("url")
    def onchange_url(self):
        if self.url:
            self.source_type = "url"

    def do_import(self):
        if self.source_type == "url":
            return self.do_import_from_url()
        if self.state == "choose":
            decoded_data = base64.b64decode(self.data_file)
            return self.do_import_from_file(decoded_data)

    def get_headers(self):
        return {}

    def do_import_from_url(self):
        if not self.url:
            return
        response = requests.get(self.url, headers=self.get_headers())
        if response.status_code == 200:
            self.filename = self.url.split("/")[-1]
            return self.do_import_from_file(response.content)
        else:
            raise Exception("Error %s" % response.status_code)

    def do_import_from_file(self, file_contents):
        if self.filename.endswith(".xlsx"):
            return self._process_file_xlsx_content(file_contents)
        if self.filename.endswith(".csv"):
            return self._process_file_csv_content(file_contents)

    def _process_file_csv_content(self, file_contents):
        raise NotImplementedError()

    def _process_file_xlsx_content(self, file_contents):
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

            table_values.append(values)
            if len(table_values) > 5000:
                self._process_table_values(table_values)
                table_values = []

        table_values.pop(0)
        if not table_values:
            return
        self._process_table_values(table_values)
        _logger.info("Imported %s rows from %s", sheet.nrows, self.filename)

    def _process_table_values(self, table_values):
        for data in table_values:
            data.append(self.vendor_info_id.id)
            data.append(self.supplier_id.id)
        fields_list = self.fields_list.split(",") + ["vendor_info_id", "supplier_id"]
        self.env["vendor.product"]._load_data_in_table(table_values, fields_list)
