# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(
        self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values
    ):
        move_values = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values
        )
        if values.get("secondary_uom_id"):
            move_values["secondary_uom_id"] = values["secondary_uom_id"]
        return move_values
