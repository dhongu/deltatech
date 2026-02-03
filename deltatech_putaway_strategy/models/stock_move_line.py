from odoo import _, models
from odoo.exceptions import UserError
import logging


_logger = logging.getLogger(__name__)



class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self, force_qty=False):
        res = super()._action_assign(force_qty=force_qty)
        # Apelăm splitarea pe toate liniile de mișcare implicate
        # Facem o buclă până când nu mai sunt necesare splitări
        is_split = self.move_line_ids._split_by_putaway_capacity()
        if is_split:
            self.with_context(avoid_putaway_rules=False)._action_assign()
        return res

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in res:
            if move.location_dest_id.usage == "internal" and move.location_dest_id.max_products_leaf:
                move.location_dest_id._compute_warehouse_occupancy()
                if move.location_dest_id.current_products > move.location_dest_id.max_products_leaf:
                    raise UserError(
                        _(
                            "Location %(location)s is over capacity (%(current)s > %(max)s)",
                            location=move.location_dest_id.display_name,
                            current=move.location_dest_id.current_products,
                            max=move.location_dest_id.max_products_leaf,
                        )
                    )
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    # def _apply_putaway_strategy(self):
    #     # Suprascriem pentru a gestiona ocuparea temporară în timpul batch-ului
    #     if self._context.get("avoid_putaway_rules") or not self:
    #         return super()._apply_putaway_strategy()
    #
    #     # În Odoo 17, procesăm liniile una câte una pentru a putea folosi un context actualizat între linii
    #     additional_qty = dict(self.env.context.get("putaway_additional_qty", {}))
    #     for line in self:
    #         line.with_context(putaway_additional_qty=additional_qty, avoid_putaway_rules=True)._apply_putaway_strategy_one()
    #         # Actualizăm ocuparea pentru următoarea linie
    #         qty = line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
    #         additional_qty[line.location_dest_id.id] = additional_qty.get(line.location_dest_id.id, 0.0) + qty

    def _split_by_putaway_capacity(self):
        # Logica de splitare a liniilor care depășesc capacitatea locației
        is_split = False
        # exclude_location = self.env.context.get("exclude_location", self.env["stock.location"])
        for line in self:
            new_line  = self.env["stock.move.line"]
            if line.location_dest_id.max_products_leaf:
                # Spațiul ocupat deja (fizic + planificat în DB)
                line.location_dest_id._compute_planned_products()
                occupied = line.location_dest_id.current_products + line.location_dest_id.planned_products

                qty_available = line.location_dest_id.max_products_leaf - occupied

                if qty_available < 0:
                    is_split = True
                    rest = line.quantity - line.location_dest_id.max_products_leaf
                    line.write({"quantity": line.location_dest_id.max_products_leaf})
                    line.copy(
                        {
                            "quantity": rest,
                            "location_dest_id": line.move_id.location_dest_id.id,
                        }
                    )
                    continue

                if qty_available < line.quantity  :
                    # Excludem locația curentă din următoarea căutare de locație
                    # exclude_location += line.location_dest_id

                    is_split = True
                    rest = line.quantity - qty_available
                    # Ajustăm linia curentă la capacitatea maximă a locației
                    line.write({"quantity": qty_available})
                    # Pregătim o linie nouă pentru restul cantității
                    line.copy(
                        {
                            "quantity": rest,
                            "location_dest_id": line.move_id.location_dest_id.id,
                        }
                    )


                        # # Re-aplicăm strategia de putaway pe noua linie, excluzând locațiile pline
                        # new_line.with_context(exclude_location=exclude_location)._apply_putaway_strategy()
                        #
                        # # Dacă locația destinație a noii linii este aceeași cu cea a liniei curente,
                        # # înseamnă că nu s-a găsit o altă locație prin putaway strategy și riscăm buclă infinită.
                        # if new_line.location_dest_id != line.location_dest_id:
                        #     new_line._split_by_putaway_capacity()


        return is_split

    # def write(self, vals):
    #     if vals.get("quantity"):
    #         self._split_by_putaway_capacity()
    #     return super().write(vals)

