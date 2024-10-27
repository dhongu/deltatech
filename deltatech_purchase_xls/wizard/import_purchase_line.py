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
    search_by_default_code = fields.Boolean("Search by internal code")
    fields_list = fields.Char(
        string="Fields",
        default="product_code,default_code,product_name,quantity,price,uom_name",
        help='Fields and order in the file. Example: "product_code,product_name,quantity,price,uom_name"',
    )

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

    def get_rows(self):
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
            return False
        if self.has_header:
            table_values.pop(0)
        return table_values

    def do_import(self):
        table_values = self.get_rows()
        lines = []
        for row in table_values:
            try:
                fields_list = self.fields_list.split(",")
                values = dict(zip(fields_list, row, strict=False))
            except Exception as e:
                raise UserError(_("Invalid file format")) from e

            product_code = values.get("product_code", False)
            if not product_code:
                continue

            product_name = values.get("product_name", False)
            quantity = values.get("quantity", False)
            price = values.get("price", False)
            uom_name = values.get("uom_name", False)

            # if len(row) == 5:
            #     product_code, product_name, quantity, price, uom_name = row
            # elif len(row) == 4:
            #     product_code, product_name, quantity, price = row
            #     uom_name = False
            # else:
            #     continue
            quantity = float(quantity)
            if self.is_amount and quantity:
                price = float(price) / quantity
            else:
                try:
                    price = float(price)
                except Exception:
                    continue

            product_id = self.search_product(product_code)
            if product_id:
                # check UOM
                product_uom = product_id.uom_po_id or product_id.uom_id
                if uom_name and uom_name != product_uom.name:
                    uom = self.env["uom.uom"].search([("name", "=", uom_name)], limit=1)
                    if uom:
                        if uom != product_id.uom_po_id and uom != product_id.uom_id:
                            raise UserError(
                                _("Product %(product_name)s does not have UOM %(uom_name)s")
                                % {"product_name": product_id.name, "uom_name": uom.name}
                            )
                        product_uom = uom
            else:
                if self.new_product:
                    product_id = self.create_product(product_code, product_name, quantity, price, uom_name)
                    product_uom = product_id.uom_po_id or product_id.uom_id
                else:
                    raise UserError(_("Product %s not found") % product_code)

            lines += [
                {
                    "order_id": self.purchase_id.id,
                    "product_id": product_id.id,
                    "name": product_name or product_id.display_name,
                    "product_qty": quantity,
                    "price_unit": price,
                    "product_uom": product_uom.id,
                    "date_planned": self.purchase_id.date_order,
                }
            ]
        purchase_lines = self.env["purchase.order.line"].create(lines)
        purchase_lines._compute_tax_id()
        if "price" not in self.fields_list:
            purchase_lines._onchange_quantity()

    def search_product(self, code=False):
        """
        Search for product by code. If supplier code not found internal code is searched,
        :param code: code to search
        :return: product record or False if not found
        """
        domain = [("product_code", "=", code)]
        supplier_info = self.env["product.supplierinfo"].sudo().search(domain, limit=1)
        if not supplier_info:
            if self.search_by_default_code:
                domain = [("default_code", "=", code)]
                product = self.env["product.product"].sudo().search(domain, limit=1)
                if product:
                    return product
                else:
                    return False
            else:
                return False
        else:
            if supplier_info.product_id:
                product = supplier_info.product_id
            else:
                product = supplier_info.product_tmpl_id.product_variant_id
            return product

    def create_product(self, product_code, product_name, quantity, price, uom_name=False):
        """
        :param product_code: code
        :param product_name: name
        :param quantity: qty to order
        :param price: price
        :param uom_name: optional, default uom(1) is set if not present
        :return: product record
        """
        seller_values = {
            "partner_id": self.purchase_id.partner_id.id,
            "product_code": product_code,
            "price": price,
            "currency_id": self.purchase_id.currency_id.id,
        }
        uom = self.env["uom.uom"].search([("name", "=", uom_name)], limit=1)
        if uom:
            uom_id = uom.id
        else:
            uom_id = 1
        values = {
            "is_storable": True,
            "name": product_name,
            "seller_ids": [(0, 0, seller_values)],
            "uom_po_id": uom_id,
            "uom_id": uom_id,
        }
        product_tmpl_id = self.env["product.template"].create(values)
        product_id = product_tmpl_id.product_variant_id
        return product_id
