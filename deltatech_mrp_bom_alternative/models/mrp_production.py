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
                    move._get_alternative_free_qty(product, allocated), move.uom_id, round=False
                )
                covered = min(unreserved, free_qty)
                allocated[product] = allocated.get(product, 0.0) + move.uom_id._compute_quantity(
                    covered, product.uom_id, round=False
                )
                shortage = unreserved - covered
                if move.uom_id.compare(shortage, 0) <= 0:
                    continue
                for alternative in move.bom_line_id._get_valid_alternatives(date):
                    alt_product = alternative.product_id
                    alt_free = move._get_alternative_free_qty(alt_product, allocated)
                    max_original = alternative._to_original_qty(alt_free, alt_product.uom_id, move.uom_id)
                    if partial:
                        qty = min(shortage, max_original)
                    elif move.uom_id.compare(max_original, shortage) >= 0:
                        qty = shortage
                    else:
                        continue
                    if move.uom_id.compare(qty, 0) <= 0:
                        continue
                    alt_qty = alternative._from_original_qty(qty, move.uom_id)
                    allocated[alt_product] = allocated.get(
                        alt_product, 0.0
                    ) + alternative.product_uom_id._compute_quantity(alt_qty, alt_product.uom_id, round=False)
                    move_exists = move.uom_id.compare(move.product_uom_qty - qty, 0) > 0
                    move._substitute_with_alternative(alternative, qty, "auto")
                    shortage -= qty
                    if not move_exists or move.uom_id.compare(shortage, 0) <= 0:
                        break

    def _get_consumption_issues(self):
        issues = super()._get_consumption_issues()
        substituted = self.move_raw_ids.filtered(lambda m: m.bom_line_alternative_id and m.state != "cancel")
        if not substituted or self.env.context.get("skip_consumption"):
            return issues
        # the moves of a substituted BoM line share its expected quantity, in proportion to their demand
        lines_by_order = {}
        for move in substituted:
            lines_by_order.setdefault(move.raw_material_production_id, set()).add(move.bom_line_id)
        result = [
            issue for issue in issues if not issue[3] or issue[3].bom_line_id not in lines_by_order.get(issue[0], ())
        ]
        for order, lines in lines_by_order.items():
            if order not in self:
                continue
            factors = order._get_bom_alternative_factors()
            for line in lines:
                moves = order.move_raw_ids.filtered(lambda m, line=line: m.bom_line_id == line and m.state != "cancel")
                demands = {move: move._get_bom_alternative_original_qty(move.product_uom_qty) for move in moves}
                total = sum(demands.values())
                expected_line = line.product_qty * factors.get(line.bom_id.id, 0.0)
                for move in moves:
                    share = expected_line * demands[move] / total if total else 0.0
                    if move.bom_line_alternative_id:
                        expected = move.bom_line_alternative_id.product_uom_id._compute_quantity(
                            move.bom_line_alternative_id._from_original_qty(share, line.uom_id), move.uom_id
                        )
                    else:
                        expected = line.uom_id._compute_quantity(share, move.uom_id)
                    picked = sum(
                        ml.uom_id._compute_quantity(ml.quantity, move.uom_id, round=False) for ml in move.move_line_ids
                    )
                    if move.uom_id.compare(picked, expected):
                        result.append((order, move.product_id, move.uom_id, move, picked, expected))
        return result

    def _get_bom_alternative_factors(self):
        """BoM factors per BoM id, as computed by ``_get_consumption_issues`` in ``mrp``."""
        self.ensure_one()
        if self.env.context.get("close_production") or self.picking_type_id.create_backorder == "never":
            qty_producing = self.product_qty
        else:
            qty_producing = self.qty_producing
        bom_factor = qty_producing / self.bom_id.uom_id._compute_quantity(
            self.bom_id.product_qty, self.uom_id, round=False
        )
        factors = {}
        for bom, data in self.bom_id.explode(self.bom_id.product_id, self.product_qty)[0]:
            if bom.type == "phantom" or bom == self.bom_id:
                factors[bom.id] = bom_factor * data["qty"] / data["original_qty"]
        return factors
