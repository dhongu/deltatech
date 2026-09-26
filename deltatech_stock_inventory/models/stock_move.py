# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    inventory_id = fields.Many2one("stock.inventory", "Inventory Document", check_company=True)
    inventory_line_id = fields.Many2one(
        "stock.inventory.line",
        "Inventory Line",
        index="btree_not_null",
        help="Inventory line that generated this move; links the accounting value back to the line.",
    )

    def _get_value_from_std_price(self, quantity, std_price=False):
        # Plusul de inventar intra la pretul de pe linie, fara sa rescrie costul produsului
        line = self.inventory_line_id
        if line and line._use_inventory_price():
            return {
                "value": line.standard_price * quantity,
                "quantity": quantity,
                "description": self.env._(
                    "%(quantity)s %(uom)s at inventory price (%(inventory)s)",
                    quantity=quantity,
                    uom=self.product_id.uom_id.name,
                    inventory=line.inventory_id.name,
                ),
            }
        return super()._get_value_from_std_price(quantity, std_price=std_price)
