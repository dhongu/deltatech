# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class Inventory(models.Model):
    _inherit = "stock.inventory"

    def _get_inventory_lines_values(self):
        lines = super()._get_inventory_lines_values()
        lot = False
        for line in lines:
            if line["prod_lot_id"]:
                lot = self.env["stock.production.lot"].browse(line["prod_lot_id"])
            if lot:
                # verificare tracking, daca e serial e posibil sa aiba reevaluari
                if lot.product_id.tracking == "serial":
                    line["standard_price"] = lot.inventory_value
                else:
                    line["standard_price"] = lot.unit_price

        return lines


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    standard_price = fields.Float(string="Price")

    @api.onchange("product_id", "location_id", "product_uom_id", "prod_lot_id", "partner_id", "package_id")
    def _onchange_quantity_context(self):
        super()._onchange_quantity_context()
        if self.prod_lot_id and self.prod_lot_id.unit_price:
            self.standard_price = self.prod_lot_id.unit_price

    def _generate_moves(self):
        for line in self:
            if line.prod_lot_id:
                line.prod_lot_id.write({"unit_price": line.standard_price})
                if line.prod_lot_id.product_id.tracking == "serial":
                    line.prod_lot_id.write({"inventory_value": line.standard_price})
            if line.difference_qty:
                lot_inventory_value = line.standard_price * line.product_qty
                line.prod_lot_id.write({"inventory_value": lot_inventory_value})
        return super()._generate_moves()
