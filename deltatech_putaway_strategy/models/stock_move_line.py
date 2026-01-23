from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _apply_putaway_strategy(self):
        # Suprascriem pentru a gestiona ocuparea temporară în timpul batch-ului
        if self._context.get("avoid_putaway_rules") or not self:
            return super()._apply_putaway_strategy()

        # Dacă avem mai mult de o linie, procesăm cu urmărirea ocupării
        if len(self) > 1:
            temp_occupancy = dict(self.env.context.get("putaway_additional_qty", {}))
            for sml in self:
                # Actualizăm contextul cu ocuparea temporară acumulată
                sml_with_context = sml.with_context(putaway_additional_qty=temp_occupancy)
                super(StockMoveLine, sml_with_context)._apply_putaway_strategy()
                # După ce s-a aplicat strategia, actualizăm ocuparea temporară cu noua destinație
                loc_id = sml.location_dest_id.id
                qty = sml.product_uom_id._compute_quantity(sml.quantity, sml.product_id.uom_id)
                temp_occupancy[loc_id] = temp_occupancy.get(loc_id, 0.0) + qty
        else:
            return super()._apply_putaway_strategy()
