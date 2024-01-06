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

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", [])
        model = self.env.context.get("active_model", False)
        purchase = self.env[model].browse(active_id)
        if purchase.state != "draft":
            raise UserError(_("The order is in the %s state") % (purchase.state))
        defaults["purchase_id"] = purchase.id
        return defaults

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

        if not table_values:
            return
        if self.has_header:
            table_values.pop(0)

        lines = []
        for row in table_values:
            if len(row) == 5:
                product_code, product_name, quantity, price, uom_name = row
            elif len(row) == 4:
                product_code, product_name, quantity, price = row
                uom_name = False
            else:
                continue

            product_id = False
            quantity = float(quantity)
            if self.is_amount and quantity:
                price = float(price) / quantity
            else:
                price = float(price)
            domain = [("product_code", "=", product_code)]
            supplierinfo = self.env["product.supplierinfo"].sudo().search(domain, limit=1)
            if not supplierinfo:
                if self.new_product:
                    seller_values = {
                        "name": self.purchase_id.partner_id.id,
                        "product_code": product_code,
                        "price": price,
                    }
                    values = {"type": "product", "name": product_name, "seller_ids": [(0, 0, seller_values)]}
                    product_tmpl_id = self.env["product.template"].create(values)
                    product_id = product_tmpl_id.product_variant_id
                else:
                    raise UserError(_("Product %s not found") % product_code)
            else:
                if supplierinfo.product_id:
                    product_id = supplierinfo.product_id
                else:
                    product_id = supplierinfo.product_tmpl_id.product_variant_id

            product_uom = product_id.uom_po_id or product_id.uom_id
            if uom_name and uom_name != product_uom.name:
                uom = self.env["uom.uom"].serach([("name", "=", uom_name)], limit=1)
                if uom:
                    product_uom = uom

            lines += [
                {
                    "order_id": self.purchase_id.id,
                    "product_id": product_id.id,
                    "name": product_name,
                    "product_qty": quantity,
                    "price_unit": price,
                    "product_uom": product_uom.id,
                    "date_planned": self.purchase_id.date_order,
                }
            ]

        self.env["purchase.order.line"].create(lines)
