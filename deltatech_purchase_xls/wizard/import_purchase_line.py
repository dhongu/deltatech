import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class ImportPurchaseLine(models.TransientModel):
    _name = "import.purchase.line"
    _description = "Import purchase line"

    data_file = fields.Binary(string="File", required=True)
    filename = fields.Char("File Name")
    has_header = fields.Boolean("Header row")
    new_product = fields.Boolean("Create missing product")
    is_amount = fields.Boolean("Is amount")
    purchase_id = fields.Many2one("purchase.order")
    product_code_is_barcode = fields.Boolean(string="Product code is barcode")

    @api.model
    def default_get(self, fields_list):
        defaults = super(ImportPurchaseLine, self).default_get(fields_list)
        active_id = self.env.context.get("active_id", [])
        model = self.env.context.get("active_model", False)
        purchase = self.env[model].browse(active_id)
        if purchase.state != "draft":
            raise UserError(_("The order is in the %s state") % (purchase.state))
        defaults["purchase_id"] = purchase.id
        return defaults

    def get_rows(self):
        decoded_data = base64.b64decode(self.data_file)
        book = xlrd.open_workbook(file_contents=decoded_data)
        sheet = book.sheet_by_index(0)
        table_values = []
        header = None
        for row in list(map(sheet.row, range(sheet.nrows))):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(str(cell.value) if is_float else str(int(cell.value)))
                else:
                    values.append(cell.value)
            table_values.append(values)

        if not table_values:
            return False
        if self.has_header:
            header = table_values.pop(0)
        return table_values, header

    def do_import(self):

        ir_model_fields_obj = self.env["ir.model.fields"]
        row_field_dic = {}
        table_values, header = self.get_rows()
        if header:
            for idx, name_field in enumerate(header):
                if self.product_code_is_barcode and not name_field == "barcode":
                    search_field = ir_model_fields_obj.sudo().search(
                        [
                            ("model", "=", "purchase.order.line"),
                            ("name", "=", name_field),
                            ("store", "=", True),
                        ],
                        limit=1,
                    )
                    if len(search_field) == 0:
                        raise UserError(_(f"Field {name_field} does not exist in purchase.order.line"))
                row_field_dic[name_field] = {"id": idx}

        lines = []
        for row in table_values:
            if header:
                if "product_code" in row_field_dic.keys():
                    product_code = row[row_field_dic["product_code"]["id"]]
                elif "barcode" in row_field_dic.keys():
                    product_code = row[row_field_dic["barcode"]["id"]]

                if "name" in row_field_dic.keys():
                    name = row[row_field_dic["name"]["id"]]

                if "product_qty" in row_field_dic.keys():
                    product_qty = row[row_field_dic["product_qty"]["id"]]

                if "price_unit" in row_field_dic.keys():
                    price_unit = row[row_field_dic["price_unit"]["id"]]

                if "product_uom" in row_field_dic.keys():
                    uom_name = row[row_field_dic["product_uom"]["id"]]
            else:
                if len(row) == 5:
                    product_code, name, product_qty, price_unit, uom_name = row
                elif len(row) == 4:
                    product_code, name, product_qty, price_unit = row
                    uom_name = False
                else:
                    continue

            product_id = False
            product_qty = float(product_qty)
            if self.is_amount and product_qty:
                price_unit = float(price_unit) / product_qty
            else:
                price_unit = float(price_unit)
            domain = [("product_code", "=", product_code)]
            supplierinfo = self.env["product.supplierinfo"].sudo().search(domain, limit=1)
            if not supplierinfo:
                if self.new_product:
                    seller_values = {
                        "name": self.purchase_id.partner_id.id,
                        "product_code": product_code,
                        "price": price_unit,
                    }
                    uom = self.env["uom.uom"].search([("name", "=", uom_name)], limit=1)
                    if uom:
                        uom_id = uom.id
                    else:
                        uom_id = 1

                    values = {
                        "type": "product",
                        "name": name,
                        "seller_ids": [(0, 0, seller_values)],
                        "uom_po_id": uom_id,
                        "uom_id": uom_id,
                    }

                    product_tmpl_id = []

                    if self.product_code_is_barcode:
                        values["barcode"] = product_code
                        product_tmpl_id = self.env["product.template"].search(
                            [("barcode", "=", values["barcode"])], limit=1
                        )

                    if len(product_tmpl_id) == 0:
                        product_tmpl_id = self.env["product.template"].create(values)

                    product_id = product_tmpl_id.product_variant_id

                else:
                    product_tmpl_id = self.env["product.template"].search([("barcode", "=", product_code)], limit=1)
                    if len(product_tmpl_id) == 0:
                        raise UserError(_("Product %s not found") % product_code)
                    else:
                        values = {}
            else:
                if supplierinfo.product_id:
                    product_id = supplierinfo.product_id
                else:
                    product_id = supplierinfo.product_tmpl_id.product_variant_id

            product_uom = product_id.uom_po_id or product_id.uom_id
            if uom_name and uom_name != product_uom.name:
                uom = self.env["uom.uom"].search([("name", "=", uom_name)], limit=1)
                if uom:
                    if uom != product_id.uom_po_id and uom != product_id.uom_id:
                        raise UserError(_("Product %s does not have UOM %s") % (product_id.name, uom.name))
                    product_uom = uom
            lines += [
                {
                    "order_id": self.purchase_id.id,
                    "product_id": product_id.id,
                    "name": product_tmpl_id.name,
                    "product_qty": product_qty,
                    "price_unit": price_unit,
                    "product_uom": product_uom.id,
                    "date_planned": self.purchase_id.date_order,
                }
            ]

        purchase_lines = self.env["purchase.order.line"].create(lines)
        purchase_lines._compute_tax_id()
