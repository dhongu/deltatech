import logging
import time

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self, force_qty=False):
        """Suprascrie atribuirea pentru a aplica automat splitarea liniilor de mișcare
        în funcție de capacitatea locațiilor de destinație.

        Suplimentar, pentru livrările al căror tip de operație are activ
        `avoid_root_location_on_reservation`, locația sursă (rădăcina depozitului,
        ex. `D1/S`) este exclusă din rezervare: marfa care nu a fost încă pusă la raft
        nu trebuie alocată automat pe vânzări. Excluderea se transmite prin cheia de
        context `exclude_location_ids`, consumată de `deltatech_stock_removal_priority`
        în `_get_gather_domain`. Filtrul este `not in` (potrivire exactă), deci
        sublocațiile (rafturile) rămân eligibile pentru rezervare.
        """
        start_time = time.time()

        # Excluderea se calculează per livrare, nu global pe recordset: dacă
        # `_action_assign` primește mișcări din mai multe tipuri de operație, doar
        # locațiile tipurilor care au flagul activ trebuie excluse.
        exclude_location_ids = self.picking_id.filtered(
            lambda p: p.picking_type_id.code == "outgoing" and p.picking_type_id.avoid_root_location_on_reservation
        ).location_id.ids
        if exclude_location_ids:
            self = self.with_context(exclude_location_ids=exclude_location_ids)

        res = super()._action_assign(force_qty=force_qty)
        # Apelăm splitarea pe toate liniile de mișcare implicate
        # Facem o buclă până când nu mai sunt necesare splitări

        lines_to_process = self.move_line_ids

        while lines_to_process:
            # per-reservation tracing: useful when debugging a putaway split, but it runs on
            # every _action_assign - 8.150 lines in 16h of production, for nothing an operator
            # or a reader of the log ever acts on. DEBUG keeps it available with --log-level.
            _logger.debug("Processing %d move lines", len(lines_to_process))
            is_split, to_reprocess = lines_to_process._split_by_putaway_capacity()
            if is_split:
                # Dacă am făcut split, verificăm să nu fi intrat într-o buclă infinită
                if lines_to_process == to_reprocess:
                    raise UserError(self.env._("Cannot assign move lines to locations"))
                lines_to_process = to_reprocess
            else:
                lines_to_process = False

        # Curățăm liniile care au rămas cu cantitate zero în urma splitării
        lines_with_zero_qty = self.move_line_ids.filtered(lambda line: line.quantity == 0)
        if lines_with_zero_qty:
            lines_with_zero_qty.unlink()

        _logger.debug("_action_assign executed in %.3f seconds", time.time() - start_time)
        return res

    def _action_done(self, cancel_backorder=False):
        """La finalizarea mișcării, verificăm încă o dată dacă nu s-a depășit capacitatea.
        Aceasta este o ultimă barieră de siguranță împotriva depășirii limitelor.
        """
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in res:
            location_dest = move.location_dest_id
            if location_dest.usage == "internal" and location_dest.max_products_leaf:
                # `current_products` / `max_products` sunt compute *nestocate*. Apelarea directă a
                # metodei de compute se face în afara mașinăriei ORM, deci atribuirile din ea nu
                # mai umplu doar cache-ul: devin `write()` real pe `stock.location`. Asta cere
                # drepturi de Inventory/Administrator și bloca validarea transferurilor pentru un
                # simplu utilizator de stoc (`stock.group_stock_user`). Pe deasupra, valoarea era
                # oricum recalculată la citirea de mai jos, care se făcea pe alt env.
                # Corect: invalidăm cache-ul și lăsăm ORM-ul să calculeze la citire, pe același
                # recordset. `sudo()` fiindcă sunt metrici derivate din quant-uri (deja citite cu
                # sudo în interiorul compute-ului), nu date de business.
                location_dest = location_dest.sudo()
                location_dest.invalidate_recordset(["current_products", "max_products", "occupancy_ratio"])
                if location_dest.current_products > location_dest.max_products_leaf:
                    raise UserError(
                        self.env._(
                            "Location %(location)s is over capacity (%(current)s > %(max)s)",
                            location=location_dest.display_name,
                            current=location_dest.current_products,
                            max=location_dest.max_products_leaf,
                        )
                    )
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _apply_putaway_strategy(self):
        if self.env.context.get("avoid_putaway_rules") or not self:
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
                # Spațiul ocupat deja (fizic + planificat în DB). Vezi nota din `_action_done`:
                # compute-urile nestocate se citesc prin ORM, nu se apelează direct, altfel
                # atribuirile din ele devin `write()` pe stock.location și cer drepturi de
                # administrator de stoc. Citirea se face acum pe *același* recordset pe care se
                # aplică `exclude_move_line_id`, altfel contextul nu avea niciun efect.
                location_dest = line.location_dest_id.sudo().with_context(exclude_move_line_id=line.id)
                location_dest.invalidate_recordset(["current_products", "planned_products"])
                occupied = location_dest.current_products + location_dest.planned_products

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
