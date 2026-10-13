from odoo import models

TARGET_KEY = "transfer_product_target_picking_id"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        target_id = self.env.context.get(TARGET_KEY)
        if target_id:
            target = self.browse(target_id) - self
            if target and target.state not in ("done", "cancel"):
                self._complete_replacement_target(target)
        return res

    def _complete_replacement_target(self, target):
        """Validate the replacement leg for the quantity actually removed by the source leg.

        The source leg is validated first (with the native backorder confirmation, if any);
        the replacement mirrors its done quantity and its backorder decision.
        """
        # executed quantity, not demand: without a backorder the done move keeps its original demand
        done_qty = sum(
            move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
            for move in self.move_ids.filtered(lambda m: m.state == "done")
        )
        if not done_qty:
            return
        target_move = target.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))[:1]
        target_qty = target_move.product_id.uom_id._compute_quantity(done_qty, target_move.product_uom)
        target_move.quantity = min(target_qty, target_move.product_uom_qty)
        target_move.picked = True
        no_backorder = self.env.context.get("cancel_backorder")
        target.with_context(
            **{TARGET_KEY: False},
            button_validate_picking_ids=target.ids,
            skip_backorder=True,
            picking_ids_not_to_backorder=target.ids if no_backorder else [],
        ).button_validate()
