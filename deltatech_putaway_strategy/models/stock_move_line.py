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
        start_time = time.time()
        res = super()._action_assign(force_qty=force_qty)
        if not self:
            return res
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

        _logger.info("_action_assign executed in %.3f seconds", time.time() - start_time)
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
        start_time = time.time()
        is_split = False
        exclude_location = self.env.context.get("exclude_location", self.env["stock.location"])
        to_reprocess = self.env["stock.move.line"]
        new_lines = self.env["stock.move.line"]

        # Prefetch în batch pentru toate locațiile implicate
        # Folosim contextul pentru a exclude liniile curente din calculul planned_products
        # pentru a avea o imagine a ocupării de către ALTE linii înainte de procesarea curentă.
        locations = self.location_dest_id
        locations.with_context(exclude_move_line_ids=self.ids).read(
            ["current_products", "planned_products", "max_products_leaf"]
        )

        # Dicționar pentru a urmări ajustările locale (delta) în timpul buclei
        # (necesar dacă mai multe linii din batch merg în aceeași locație)
        local_adjustments = {}

        for line in self:
            loc = line.location_dest_id.with_context(exclude_move_line_ids=self.ids)
            if not loc.max_products_leaf:
                continue

            # 'planned_products' NU conține 'line_qty' (pentru că am folosit exclude_move_line_ids în read)
            others_occupied = loc.current_products + loc.planned_products

            # Adăugăm ajustările făcute de liniile procesate anterior în această buclă
            adjustment = local_adjustments.get(loc.id, 0.0)

            occupied_total = others_occupied + adjustment
            qty_available = loc.max_products_leaf - occupied_total

            if qty_available <= 0:
                # Locația este deja plină sau depășită de alte mișcări
                _logger.warning("Location %s is not available anymore", loc.display_name)
                exclude_location += loc
                is_split = True
                rest = line.quantity
                if rest > 0:
                    line.write({"quantity": 0})
                    # Creăm o copie a liniei pe care o vom trimite la o altă locație
                    new_lines |= line.copy(
                        {
                            "quantity": rest,
                            "location_dest_id": line.move_id.location_dest_id.id,
                        }
                    )
                continue

            if qty_available < line.quantity:
                # Locația poate primi doar o parte din cantitate
                exclude_location += loc

                is_split = True
                rest = line.quantity - qty_available
                # Ajustăm linia curentă la spațiul disponibil
                line.write({"quantity": qty_available})

                # Actualizăm ajustarea locală: consumăm exact qty_available
                local_adjustments[loc.id] = adjustment + qty_available

                # Creăm o linie nouă pentru restul cantității, care va căuta altă locație
                new_lines |= line.copy(
                    {
                        "quantity": rest,
                        "location_dest_id": line.move_id.location_dest_id.id,
                    }
                )
            else:
                # Linia încape complet, actualizăm delta pentru următoarele linii din același batch
                local_adjustments[loc.id] = adjustment + line.quantity

        if new_lines:
            # Pentru noile linii generate, reaplicăm strategia de putaway excluzând locațiile deja pline
            new_lines.with_context(exclude_location=exclude_location)._apply_putaway_strategy()
            to_reprocess |= new_lines

        _logger.info("_split_by_putaway_capacity executed in %.3f seconds", time.time() - start_time)
        return is_split, to_reprocess


