# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    standard_price = fields.Float(string="Price")

    def _onchange_quantity_context(self):
        super(InventoryLine, self)._onchange_quantity_context()
        if self.prod_lot_id and self.prod_lot_id.unit_price:
            self.standard_price = self.prod_lot_id.unit_price

    def _generate_moves(self):
        for line in self:
            if line.prod_lot_id and line.prod_lot_id.unit_price != line.standard_price:
                line.prod_lot_id.write({"unit_price": line.standard_price})
        return super(InventoryLine, self)._generate_moves()
