import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self, force_qty=False):
        """Suprascrie atribuirea pentru a aplica automat splitarea liniilor de mișcare
        în funcție de capacitatea locațiilor de destinație.
        """

        pickings = self.mapped("picking_id")

        if pickings:
            # Luăm în considerare doar tipurile OUT (livrări)
            pickings_out = pickings.filtered(lambda p: p.picking_type_id.code == "outgoing")
            if any(pickings_out.mapped("picking_type_id.avoid_root_location_on_reservation")):
                exclude_location_ids = pickings_out.mapped("location_id").ids
                self = self.with_context(exclude_location_ids=exclude_location_ids)

        res = super()._action_assign(force_qty=force_qty)
        if self._context.get("avoid_putaway_rules"):
            return res

        if any(pickings.mapped("picking_type_id.avoid_putaway_rules")):
            return res

        # Apelăm splitarea pe toate liniile de mișcare implicate
        # Facem o buclă până când nu mai sunt necesare splitări

        lines_to_process = self.move_line_ids

        while lines_to_process:
            _logger.info("Processing %d move lines", len(lines_to_process))
            is_split, to_reprocess = lines_to_process._split_by_putaway_capacity()
            if is_split:
                # Dacă am făcut split, verificăm să nu fi intrat într-o buclă infinită
                if lines_to_process == to_reprocess:
                    raise UserError(_("Cannot assign move lines to locations"))
                lines_to_process = to_reprocess
            else:
                lines_to_process = False

        # Curățăm liniile care au rămas cu cantitate zero în urma splitării
        lines_with_zero_qty = self.move_line_ids.filtered(lambda line: line.quantity == 0)
        if lines_with_zero_qty:
            lines_with_zero_qty.unlink()

        return res

    def _action_done(self, cancel_backorder=False):
        """La finalizarea mișcării, verificăm încă o dată dacă nu s-a depășit capacitatea.
        Aceasta este o ultimă barieră de siguranță împotriva depășirii limitelor.
        """
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

    def _apply_putaway_strategy(self):
        if self._context.get("avoid_putaway_rules") or not self:
            return super()._apply_putaway_strategy()
        if any(self.mapped("picking_type_id.avoid_putaway_rules")):
            return super(StockMoveLine, self.with_context(avoid_putaway_rules=True))._apply_putaway_strategy()

        return super()._apply_putaway_strategy()

    def _split_by_putaway_capacity(self):
        # Logica de splitare a liniilor care depășesc capacitatea locației
        is_split = False
        exclude_location = self.env.context.get("exclude_location", self.env["stock.location"])
        to_reprocess = self.env["stock.move.line"]
        new_lines = self.env["stock.move.line"]
        for line in self:
            if line.location_dest_id.max_products_leaf:
                # Spațiul ocupat deja (fizic + planificat în DB)
                line.location_dest_id.with_context(exclude_move_line_id=line.id).sudo()._compute_planned_products()
                occupied = line.location_dest_id.current_products + line.location_dest_id.planned_products

                qty_available = line.location_dest_id.max_products_leaf - occupied

                if qty_available < 0:
                    # locatia aleasa nu mai este disponibila
                    _logger.warning("Location %s is not available anymore", line.location_dest_id.display_name)
                    exclude_location += line.location_dest_id
                    is_split = True
                    rest = line.quantity
                    line.write({"quantity": 0})

                    new_lines |= line.copy(
                        {
                            "quantity": rest,
                            "location_dest_id": line.move_id.location_dest_id.id,
                        }
                    )
                    continue

                if qty_available and qty_available < line.quantity:
                    # Excludem locația curentă din următoarea căutare de locație
                    exclude_location += line.location_dest_id

                    is_split = True
                    rest = line.quantity - qty_available
                    # Ajustăm linia curentă la capacitatea maximă a locației
                    line.write({"quantity": qty_available})
                    # Pregătim o linie nouă pentru restul cantității
                    new_lines |= line.copy(
                        {
                            "quantity": rest,
                            "location_dest_id": line.move_id.location_dest_id.id,
                        }
                    )

        if new_lines:
            new_lines.with_context(exclude_location=exclude_location)._apply_putaway_strategy()
            to_reprocess |= new_lines
        return is_split, to_reprocess
