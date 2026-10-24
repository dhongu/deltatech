from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_confirm(self):
        # before super: the scheduler run by the confirmation must already see the substituted components
        self.filtered(lambda p: p.state == "draft")._apply_bom_alternatives()
        return super().action_confirm()

    def action_assign(self):
        res = super().action_assign()
        self.filtered(
            lambda p: p.state in ("confirmed", "progress", "to_close") and p.company_id.mrp_alternative_on_assign
        )._apply_bom_alternatives()
        return res

    def _get_bom_alternative_moves(self):
        return self.move_raw_ids.filtered(
            lambda m: m.state not in ("done", "cancel")
            and not m.picked
            and not m.bom_line_alternative_id
            and m.bom_line_id.alternative_policy == "auto"
            and m.bom_line_id.alternative_ids
            and m.product_id.is_storable
            and m.procure_method == "make_to_stock"
        )

    def _apply_bom_alternatives(self):
        """Cover the shortage of the components with an automatic policy from their alternatives."""
        # fresh stock figures once per run; inside the run the cache plus ``allocated`` avoid counting twice
        self.env["product.product"].invalidate_model(["free_qty"])
        allocated = {}
        for production in self:
            date = fields.Date.to_date(production.date_start) or fields.Date.context_today(production)
            partial = production.company_id.mrp_alternative_partial
            for move in production._get_bom_alternative_moves():
                product = move.product_id
                reserved = move.quantity if move.state != "draft" else 0.0
                unreserved = move.product_uom_qty - reserved
                free_qty = product.uom_id._compute_quantity(
                    move._get_alternative_free_qty(product, allocated), move.product_uom, round=False
                )
                covered = min(unreserved, free_qty)
                allocated[product] = allocated.get(product, 0.0) + move.product_uom._compute_quantity(
                    covered, product.uom_id, round=False
                )
                shortage = unreserved - covered
                if move.product_uom.compare(shortage, 0) <= 0:
                    continue
                for alternative in move.bom_line_id._get_valid_alternatives(date):
                    alt_product = alternative.product_id
                    alt_free = move._get_alternative_free_qty(alt_product, allocated)
                    max_original = alternative._to_original_qty(alt_free, alt_product.uom_id, move.product_uom)
                    if partial:
                        qty = min(shortage, max_original)
                    elif move.product_uom.compare(max_original, shortage) >= 0:
                        qty = shortage
                    else:
                        continue
                    if move.product_uom.compare(qty, 0) <= 0:
                        continue
                    alt_qty = alternative._from_original_qty(qty, move.product_uom)
                    allocated[alt_product] = allocated.get(
                        alt_product, 0.0
                    ) + alternative.product_uom_id._compute_quantity(alt_qty, alt_product.uom_id, round=False)
                    move_exists = move.product_uom.compare(move.product_uom_qty - qty, 0) > 0
                    move._substitute_with_alternative(alternative, qty, "auto")
                    shortage -= qty
                    if not move_exists or move.product_uom.compare(shortage, 0) <= 0:
                        break

    def _get_moves_raw_values(self):
        moves = super()._get_moves_raw_values()
        if not self.env.context.get("mrp_alternative_expected"):
            return moves
        # expected consumption: the substituted part of a BoM line moves to its alternative
        for production in self:
            for move in production.move_raw_ids.filtered(lambda m: m.bom_line_alternative_id and m.state != "cancel"):
                alternative = move.bom_line_alternative_id
                for values in moves:
                    if (
                        values.get("raw_material_production_id") == production.id
                        and values.get("bom_line_id") == move.bom_line_id.id
                        and not values.get("bom_line_alternative_id")
                    ):
                        uom = self.env["uom.uom"].browse(values["product_uom"])
                        replaced = alternative._to_original_qty(move.product_uom_qty, move.product_uom, uom)
                        values["product_uom_qty"] = max(values["product_uom_qty"] - replaced, 0.0)
                        break
                alt_values = production._get_move_raw_values(
                    move.product_id, move.product_uom_qty, move.product_uom, move.operation_id.id, move.bom_line_id
                )
                alt_values["bom_line_alternative_id"] = alternative.id
                moves.append(alt_values)
        return moves

    def _get_consumption_issues(self):
        return super(MrpProduction, self.with_context(mrp_alternative_expected=True))._get_consumption_issues()
