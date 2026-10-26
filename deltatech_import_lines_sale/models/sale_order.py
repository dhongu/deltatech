# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command, api, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "import.lines.mixin"]

    def _import_lines_check(self):
        self.ensure_one()
        if self.state not in ("draft", "sent"):
            raise UserError(self.env._("Lines can be imported only in quotations."))
        return True

    @api.model
    def _import_lines_targets(self):
        return super()._import_lines_targets() + ["price_unit", "discount"]

    def _import_lines_partner(self):
        return self.partner_id

    def _import_lines_company(self):
        return self.company_id

    def _import_lines_product_domain(self):
        return super()._import_lines_product_domain() + [("sale_ok", "=", True)]

    def _import_lines_prepare_line(self, row):
        vals = {"product_id": row["product"].id, "product_uom_qty": row["quantity"]}
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
