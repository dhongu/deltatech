# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.exceptions import UserError


class ImportLinesMixin(models.AbstractModel):
    """Contract between the import lines wizard and a document.

    A document model inherits this mixin and overrides the hooks below; the wizard holds no
    document specific logic. The hooks are called on the document (one record) or, for documents
    without a header record (inventory), on an empty recordset of the model.
    """

    _name = "import.lines.mixin"
    _description = "Import Lines Mixin"

    def _import_lines_check(self):
        """Raise a UserError when lines cannot be imported in the document in its current state."""
        return True

    @api.model
    def _import_lines_targets(self):
        """Column targets the document uses (keys of the wizard column ``target`` selection)."""
        return ["product", "quantity", "uom", "description"]

    @api.model
    def _import_lines_match_keys(self):
        """Product match keys the document accepts (keys of the wizard ``match_by`` selection)."""
        return ["default_code", "barcode", "name"]

    def _import_lines_partner(self):
        """Partner of the document, used to choose the saved column mapping."""
        return self.env["res.partner"]

    def _import_lines_company(self):
        return self.env.company

    def _import_lines_product_domain(self):
        company = self._import_lines_company()
        return [("company_id", "in", [company.id, False])]

    def _import_lines_find_product(self, match_by, value):
        """Return the products matching ``value``; more than one product means an ambiguous row."""
        Product = self.env["product.product"]
        domain = self._import_lines_product_domain()
        if match_by == "default_code":
            return Product.search(domain + [("default_code", "=", value)], limit=2)
        if match_by == "barcode":
            return Product.search(domain + [("barcode", "=", value)], limit=2)
        if match_by == "name":
            # the display name format "[CODE] Name" is resolved by the code
            if value.startswith("[") and "]" in value:
                code = value[1 : value.index("]")].strip()
                products = Product.search(domain + [("default_code", "=", code)], limit=2)
                if products:
                    return products
                value = value[value.index("]") + 1 :].strip()
            return Product.search(domain + [("name", "=ilike", value)], limit=2)
        return Product

    def _import_lines_find_products(self, match_by, values):
        """Return {value: products} for all the product references of the file at once.

        The internal reference and the barcode are searched in one query; the other keys fall back to
        ``_import_lines_find_product`` for each distinct value.
        """
        values = set(values)
        Product = self.env["product.product"]
        field = {"default_code": "default_code", "barcode": "barcode"}.get(match_by)
        if not field:
            return {value: self._import_lines_find_product(match_by, value) for value in values}
        result = dict.fromkeys(values, Product)
        products = Product.search(self._import_lines_product_domain() + [(field, "in", list(values))])
        for product in products:
            result[product[field]] |= product
        return result

    @api.model
    def _import_lines_allow_zero_quantity(self):
        return False

    def _import_lines_check_row(self, row):
        """Return an error ``(status, message)`` for a matched row, or False when the row is valid.

        :param row: dict with the keys ``product``, ``quantity``, ``uom``, ``lot_name`` (see the wizard)
        """
        return False

    def _import_lines_create(self, rows, wizard):
        """Create the document lines from the valid rows.

        :param rows: list of dicts with ``product``, ``quantity``, ``uom`` and, when mapped,
            ``price_unit``, ``discount``, ``lot_name``, ``description``
        :param wizard: the import wizard (for the options such as the inventory location)
        """
        raise UserError(self.env._("Importing lines is not implemented for %s.", self._description))
