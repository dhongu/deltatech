from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _apply_putaway_strategy(self):
        res = super()._apply_putaway_strategy()
        new_lines = self.env["stock.move.line"]
        exclude_location = self.env.context.get("exclude_location", self.env["stock.location"])
        for line in self:
            if line.location_dest_id.max_products_leaf:
                # se mai pot pune
                qty_available = line.location_dest_id.max_products_leaf - line.location_dest_id.current_products
                if qty_available < line.quantity:
                    exclude_location = exclude_location | line.location_dest_id
                    rest = line.quantity - qty_available
                    line.quantity = qty_available
                    new_lines += line.copy({"quantity": rest, "location_dest_id": line.move_id.location_dest_id.id})
        if new_lines:
            new_lines.with_context(exclude_location=exclude_location)._apply_putaway_strategy()
        return res
