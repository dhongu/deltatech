import logging
import time

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self, force_qty=False):
        """Suprascrie atribuirea pentru a aplica automat splitarea liniilor de mișcare
        în funcție de capacitatea locațiilor de destinație.
        """
        res = super()._action_assign(force_qty=force_qty)
        # Procesăm liniile într-o buclă pentru a gestiona splitările succesive
        # (când o locație alternativă se umple și ea)
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
            location = move.location_dest_id
            if location.usage == "internal" and location.max_products_leaf:
                occupied = location.current_products + location.planned_products
                if occupied > location.max_products_leaf:
                    raise UserError(
                        _(
                            "Location %(location)s is over capacity (%(current)s > %(max)s)",
                            location=location.display_name,
                            current=occupied,
                            max=location.max_products_leaf,
                        )
                    )
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"



    def _split_by_putaway_capacity(self):
        """Verifică fiecare linie de mișcare dacă încape în locația de destinație.
        Dacă nu încape, linia este splitată:
        - Partea care încape rămâne în locația curentă.
        - Partea care depășește capacitatea este trimisă către o nouă căutare de locație prin putaway strategy.
        """
        is_split = False
        exclude_location = self.env.context.get("exclude_location", self.env["stock.location"])
        to_reprocess = self.env["stock.move.line"]
        new_lines = self.env["stock.move.line"]
        for line in self:
            if line.location_dest_id.max_products_leaf:

                # Recalculăm cantitatea planificată pentru locația destinație, excluzând linia curentă
                # (pentru a vedea spațiul ocupat de ceilalți fără a ne număra pe noi înșine)
                line.location_dest_id.with_context(exclude_move_line_id=line.id)._compute_planned_products()
                occupied = line.location_dest_id.current_products + line.location_dest_id.planned_products

                qty_available = line.location_dest_id.max_products_leaf - occupied

                if qty_available < 0:
                    # Locația este deja plină sau depășită de alte mișcări
                    _logger.warning("Location %s is not available anymore", line.location_dest_id.display_name)
                    exclude_location += line.location_dest_id
                    is_split = True
                    rest = line.quantity
                    line.write({"quantity": 0})

                    # Creăm o copie a liniei pe care o vom trimite la o altă locație
                    new_lines |= line.copy(
                        {
                            "quantity": rest,
                            "location_dest_id": line.move_id.location_dest_id.id,
                        }
                    )
                    continue

                if qty_available and qty_available < line.quantity:
                    # Locația poate primi doar o parte din cantitate
                    exclude_location += line.location_dest_id

                    is_split = True
                    rest = line.quantity - qty_available
                    # Ajustăm linia curentă la spațiul disponibil
                    line.write({"quantity": qty_available})
                    # Creăm o linie nouă pentru restul cantității, care va căuta altă locație
                    new_lines |= line.copy(
                        {
                            "quantity": rest,
                            "location_dest_id": line.move_id.location_dest_id.id,
                        }
                    )

        if new_lines:
            # Pentru noile linii generate, reaplicăm strategia de putaway excluzând locațiile deja pline
            new_lines.with_context(exclude_location=exclude_location)._apply_putaway_strategy()
            to_reprocess |= new_lines
        return is_split, to_reprocess


