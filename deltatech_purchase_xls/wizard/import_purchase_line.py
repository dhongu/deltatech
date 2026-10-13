import base64
import io
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# todo: de folosit
# from odoo.tools.misc import xlsxwriter
# xlrd >= 2.0 nu mai citește fișiere .xlsx, deci folosim openpyxl (inclus în Odoo)
try:
    import openpyxl
except ImportError:
    openpyxl = None


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
            raise UserError(self.env._("The order is in the %s state", purchase.state))
        defaults["purchase_id"] = purchase.id
        return defaults

    def get_rows(self):
        if openpyxl is None:
            raise UserError(self.env._("The 'openpyxl' Python library is required to read .xlsx files."))
        decoded_data = base64.b64decode(self.data_file)
        book = openpyxl.load_workbook(io.BytesIO(decoded_data), data_only=True)
        sheet = book.worksheets[0]
        table_values = []
        for row in sheet.iter_rows(values_only=True):
            values = []
            for value in row:
                if value is None:
                    values.append("")
                elif isinstance(value, bool):
                    values.append(value)
                elif isinstance(value, (int, float)):
                    is_float = value % 1 != 0.0
                    values.append(str(value) if is_float else str(int(value)))
                else:
                    values.append(value)
            table_values.append(values)

        if self.has_header and table_values:
            table_values.pop(0)
        return table_values

    def do_import(self):
        table_values = self.get_rows()
        if not table_values:
            raise UserError(self.env._("The file has no rows to import."))
        first_row = 2 if self.has_header else 1
        lines = []
        for row_number, row in enumerate(table_values, start=first_row):
            try:
                fields_list = self.fields_list.split(",")
                values = dict(zip(fields_list, row, strict=False))
            except Exception as e:
                raise UserError(self.env._("Invalid file format")) from e

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
            try:
                quantity = float(quantity)
            except (TypeError, ValueError) as e:
                raise UserError(
                    self.env._(
                        'Row %(row)s: the quantity "%(quantity)s" is not a number.',
                        row=row_number,
                        quantity=quantity,
                    )
                ) from e
            try:
                price = float(price)
            except (TypeError, ValueError):
                continue
            if self.is_amount and "price" in self.fields_list:
                if quantity:
                    price = price / quantity
                elif price:
                    raise UserError(
                        self.env._(
                            "Row %(row)s: the unit price cannot be computed from the amount %(amount)s "
                            "because the quantity is zero.",
                            row=row_number,
                            amount=price,
                        )
                    )

            product_id = self.search_product(product_code)
            if product_id:
                # check UOM
                product_uom = product_id.uom_id
                if uom_name and uom_name != product_uom.name:
                    uom = self.env["uom.uom"].search([("name", "=", uom_name)], limit=1)
                    if uom:
                        if uom != product_id.uom_id:
                            raise UserError(
                                self.env._(
                                    "Product %(product_name)s does not have UOM %(uom_name)s",
                                    product_name=product_id.name,
                                    uom_name=uom.name,
                                )
                            )
                        product_uom = uom
            else:
                if self.new_product:
                    product_id = self.create_product(product_code, product_name, quantity, price, uom_name)
                    product_uom = product_id.uom_id
                else:
                    raise UserError(self.env._("Product %s not found", product_code))

            lines += [
                {
                    "order_id": self.purchase_id.id,
                    "product_id": product_id.id,
                    "name": product_name or product_id.display_name,
                    "product_qty": quantity,
                    "price_unit": price,
                    "product_uom_id": product_uom.id,
                    "date_planned": self.purchase_id.date_order,
                }
            ]
        purchase_lines = self.env["purchase.order.line"].create(lines)
        purchase_lines._compute_tax_id()
        if "price" not in self.fields_list:
            purchase_lines._compute_price_unit_and_date_planned_and_name()

    def search_product(self, code=False):
        """
        Search for product by code. If supplier code not found internal code is searched,
        :param code: code to search
        :return: product record or False if not found

        The supplier code is resolved only on the vendor pricing rows of the order vendor (or of its
        commercial partner) that apply to the order company. A code that leads to several products
        is reported instead of picking one at random.
        """
        order = self.purchase_id
        company = order.company_id or self.env.company
        domain = [("product_code", "=", code), ("company_id", "in", [company.id, False])]
        if order.partner_id:
            domain += [("partner_id", "child_of", order.partner_id.commercial_partner_id.id)]
        supplier_infos = self.env["product.supplierinfo"].sudo().search(domain)
        if not supplier_infos:
            if self.search_by_default_code:
                domain = [("default_code", "=", code), ("company_id", "in", [company.id, False])]
                product = self.env["product.product"].sudo().search(domain, limit=1)
                if product:
                    return product
                else:
                    return False
            else:
                return False
        products = self.env["product.product"]
        for supplier_info in supplier_infos:
            products |= supplier_info.product_id or supplier_info.product_tmpl_id.product_variant_ids
        if len(products) > 1:
            raise UserError(
                self.env._(
                    "The supplier code %(code)s of %(vendor)s matches several products: %(products)s. "
                    "Set the product variant on the vendor pricelist.",
                    code=code,
                    vendor=order.partner_id.display_name,
                    products=", ".join(products.mapped("display_name")),
                )
            )
        return products

    def create_product(self, product_code, product_name, quantity, price, uom_name=False):
        """
        :param product_code: code
        :param product_name: name
        :param quantity: qty to order
        :param price: price
        :param uom_name: optional, the Units UoM is set if not present
        :return: product record
        """
        seller_values = {
            "partner_id": self.purchase_id.partner_id.id,
            "product_code": product_code,
            "price": price,
            "currency_id": self.purchase_id.currency_id.id,
            "company_id": self.purchase_id.company_id.id,
        }
        uom = uom_name and self.env["uom.uom"].search([("name", "=", uom_name)], limit=1)
        uom_id = uom.id if uom else self.env.ref("uom.product_uom_unit").id
        values = {
            "is_storable": True,
            "name": product_name,
            "seller_ids": [(0, 0, seller_values)],
            "uom_id": uom_id,
        }
        product_tmpl_id = self.env["product.template"].create(values)
        product_id = product_tmpl_id.product_variant_id
        return product_id
