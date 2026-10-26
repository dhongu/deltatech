# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command, api, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = ["mrp.production", "import.lines.mixin"]

    def _import_lines_check(self):
        self.ensure_one()
        if self.state not in ("draft", "confirmed"):
            raise UserError(self.env._("Components can be imported only in draft or confirmed manufacturing orders."))
        return True

    @api.model
    def _import_lines_targets(self):
        return ["product", "quantity", "uom"]

    def _import_lines_company(self):
        return self.company_id

    def _import_lines_product_domain(self):
        return super()._import_lines_product_domain() + [("type", "=", "consu")]

    def _import_lines_check_row(self, row):
        error = super()._import_lines_check_row(row)
        if not error and row["product"] == self.product_id:
            return "not_allowed", self.env._("The product to produce cannot be a component.")
        return error

    def _import_lines_create(self, rows, wizard):
        self.ensure_one()
        commands = [
            Command.create(
                self._get_move_raw_values(row["product"], row["quantity"], row["uom"] or row["product"].uom_id)
            )
            for row in rows
        ]
        self.write({"move_raw_ids": commands})
