# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    inventory_id = fields.Many2one("stock.inventory", "Inventory")
    inventory_line_id = fields.Many2one("stock.inventory.line", "Inventory Line")

    def create_inventory_lines(self):
        inventory = False

        for quant in self:
            if not quant.inventory_id and not inventory:
                inventory = self.env["stock.inventory"].create(
                    {
                        "name": self.env.context.get("inventory_name", "/"),
                        "state": "confirm",
                    }
                )
            if not quant.inventory_id and inventory:
                quant.write({"inventory_id": inventory.id})
            if quant.inventory_id and not inventory:
                inventory = quant.inventory_id

            if quant.inventory_id != inventory:
                raise UserError(_("The selected items are in different inventories"))
            if not quant.inventory_line_id:
                line_values = {
                    "inventory_id": inventory.id,
                    "product_qty": quant.inventory_quantity,
                    "theoretical_qty": quant.quantity,
                    "prod_lot_id": quant.lot_id.id,
                    "partner_id": quant.owner_id.id,
                    "product_id": quant.product_id.id,
                    "location_id": quant.location_id.id,
                    "package_id": quant.package_id.id,
                    "is_ok": False,
                }
                inventory_line = self.env["stock.inventory.line"].create(line_values)
                quant.write({"inventory_line_id": inventory_line.id})

        return inventory

    def action_set_inventory_quantity_to_zero(self):
        self.inventory_id = False
        self.inventory_line_id = False
        super(StockQuant, self).action_set_inventory_quantity_to_zero()

    def action_apply_inventory(self):
        inventory = self.filtered(lambda q: q.inventory_quantity_set).create_inventory_lines()

        super(StockQuant, self.with_context(apply_inventory=True)).action_apply_inventory()
        for quant in self:
            inventor_line = quant.inventory_line_id
            if inventor_line:
                inventor_line.write({"is_ok": True})

        if inventory:
            date = inventory.date
            values = {"date": date, "state": "done"}
            if inventory.name in ("/", _("New")):
                sequence = self.env.ref("deltatech_stock_inventory.sequence_inventory_doc")
                if sequence:
                    values["name"] = sequence.next_by_id()

            inventory.write(values)
        self.write({"inventory_id": False, "inventory_line_id": False})

    def write(self, vals):
        res = super(StockQuant, self).write(vals)
        if "inventory_quantity" in vals and not self.env.context.get("apply_inventory", False):
            for quant in self:
                inventor_line = quant.inventory_line_id
                if inventor_line and inventor_line.product_qty != quant.inventory_quantity:
                    inventor_line.write({"product_qty": quant.inventory_quantity, "is_ok": True})
                # else:
                #     quant.create_inventory_lines()
        return res

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        values = super(StockQuant, self)._get_inventory_move_values(qty, location_id, location_dest_id, out)
        values["inventory_id"] = self.inventory_id.id
        return values
