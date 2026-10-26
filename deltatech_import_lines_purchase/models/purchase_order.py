# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command, api, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "import.lines.mixin"]

    def _import_lines_check(self):
        self.ensure_one()
        if self.state not in ("draft", "sent"):
            raise UserError(self.env._("Lines can be imported only in requests for quotation."))
        return True

    @api.model
    def _import_lines_targets(self):
        return super()._import_lines_targets() + ["price_unit", "discount"]

    @api.model
    def _import_lines_match_keys(self):
        return super()._import_lines_match_keys() + ["vendor_code"]

    def _import_lines_partner(self):
        return self.partner_id

    def _import_lines_company(self):
        return self.company_id

    def _import_lines_product_domain(self):
        return super()._import_lines_product_domain() + [("purchase_ok", "=", True)]

    def _import_lines_find_product(self, match_by, value):
        if match_by != "vendor_code":
            return super()._import_lines_find_product(match_by, value)
        company = self._import_lines_company()
        domain = [("product_code", "=", value), ("company_id", "in", [company.id, False])]
        if self.partner_id:
            domain.append(("partner_id", "child_of", self.partner_id.commercial_partner_id.id))
        products = self.env["product.product"]
        for seller in self.env["product.supplierinfo"].search(domain):
            products |= seller.product_id or seller.product_tmpl_id.product_variant_ids
        return products.filtered_domain(self._import_lines_product_domain())

    def _import_lines_prepare_line(self, row):
        vals = {"product_id": row["product"].id, "product_qty": row["quantity"]}
        if row["uom"]:
            vals["product_uom_id"] = row["uom"].id
        if "price_unit" in row:
            vals["price_unit"] = row["price_unit"]
        if "discount" in row:
            vals["discount"] = row["discount"]
        if row.get("description"):
            vals["name"] = row["description"]
        return vals

    def _import_lines_create(self, rows, wizard):
        self.ensure_one()
        self.write({"order_line": [Command.create(self._import_lines_prepare_line(row)) for row in rows]})
