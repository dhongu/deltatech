from datetime import datetime, time

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.tools import float_compare, float_is_zero, format_date

# Move states that still represent an open (not yet done/cancelled) flow, the
# same set Odoo uses when computing the forecast on an orderpoint.
OPEN_MOVE_STATES = ("waiting", "confirmed", "assigned", "partially_available")


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    def action_explain_replenishment(self):
        """Open a read-only dialog that explains how this reordering rule
        reached its forecast and to-order quantity, and what could make it
        under- or over-order (visibility / horizon risks)."""
        self.ensure_one()
        wizard = self.env["stock.replenishment.explanation"].create({"orderpoint_id": self.id})
        return {
            "type": "ir.actions.act_window",
            "name": _("Why this replenishment?"),
            "res_model": "stock.replenishment.explanation",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _explain_fmt(self, qty):
        """Format a quantity in the product UoM precision for display."""
        return self.env["ir.qweb.field.float"].value_to_html(qty, {"decimal_precision": "Product Unit"})

    def _explain_round_to_multiple(self, qty_to_order):
        """Replicate v18 _get_qty_to_order rounding to qty_multiple."""
        self.ensure_one()
        rounding = self.product_uom.rounding
        remainder = (self.qty_multiple > 0.0 and qty_to_order % self.qty_multiple) or 0.0
        if (
            float_compare(remainder, 0.0, precision_rounding=rounding) > 0
            and float_compare(self.qty_multiple - remainder, 0.0, precision_rounding=rounding) > 0
        ):
            if float_is_zero(self.product_max_qty, precision_rounding=rounding):
                qty_to_order += self.qty_multiple - remainder
            else:
                qty_to_order -= remainder
        return qty_to_order

    def _explain_scheduled_moves(self, horizon_dt, beyond_dt):
        """Return (incoming, outgoing, beyond_qty, beyond_date) open moves for
        this orderpoint's product/location: receipts and demand up to `horizon_dt`,
        plus demand scheduled after `beyond_dt` (invisible to the order forecast)."""
        self.ensure_one()
        Move = self.env["stock.move"].with_context(active_test=False)
        loc = self.location_id
        common = [
            ("product_id", "=", self.product_id.id),
            ("state", "in", OPEN_MOVE_STATES),
        ]
        incoming = sum(
            Move.search(common + [("location_dest_id", "child_of", loc.id), ("date", "<=", horizon_dt)]).mapped(
                "product_qty"
            )
        )
        outgoing = sum(
            Move.search(common + [("location_id", "child_of", loc.id), ("date", "<=", horizon_dt)]).mapped(
                "product_qty"
            )
        )
        beyond = Move.search(common + [("location_id", "child_of", loc.id), ("date", ">", beyond_dt)], order="date")
        beyond_qty = sum(beyond.mapped("product_qty"))
        beyond_date = beyond[:1].date
        return incoming, outgoing, beyond_qty, beyond_date

    def _get_global_visibility_days(self):
        return int(
            self.env.context.get(
                "global_visibility_days",
                self.env["ir.config_parameter"].sudo().get_param("stock.visibility_days", 0),
            )
        )

    def _get_replenishment_explanation(self):
        """Reconstruct, with live numbers, the computation Odoo 18 runs on this
        orderpoint and return a values dict for the QWeb explanation template."""
        self.ensure_one()
        op = self
        product = op.product_id
        rounding = op.product_uom.rounding

        # --- Lead time + its human-readable breakdown (don't bypass the description) ---
        lead_values = op._get_lead_days_values()
        delays, description = op.rule_ids.with_context(bypass_delay_description=False)._get_lead_days(
            product, **lead_values
        )
        total_delay = delays.get("total_delay", 0.0)
        no_vendor_delay = delays.get("no_vendor_found_delay", 0.0)
        global_visibility_days = op._get_global_visibility_days()
        visibility_days = op.visibility_days
        lead_days_date = op.lead_days_date
        visibility_window_date = lead_days_date + relativedelta(days=int(visibility_days)) if lead_days_date else False
        delay_rows = [(label, value) for label, value in description if isinstance(value, str)]

        # --- Quantities ---
        on_hand = op.qty_on_hand
        in_progress = op._quantity_in_progress().get(op.id, 0.0)
        gate_forecast = op.qty_forecast  # virtual_available @ lead_days_date + in_progress
        vis_ctx = op._get_product_context(visibility_days=visibility_days)
        order_forecast = (
            product.with_context(**vis_ctx).read(["virtual_available"])[0]["virtual_available"] + in_progress
        )
        min_qty = op.product_min_qty
        max_qty = op.product_max_qty
        target = max(min_qty, max_qty)

        # --- Decision (gate uses forecast @ lead time) + order quantity (uses visibility window) ---
        below_min = float_compare(gate_forecast, min_qty, precision_rounding=rounding) < 0
        raw_to_order = (target - order_forecast) if below_min else 0.0
        rounded_to_order = op._explain_round_to_multiple(raw_to_order) if below_min else 0.0

        # --- Scheduled moves: receipts/demand up to the visibility window, demand beyond it ---
        horizon_dt = (
            datetime.combine(visibility_window_date, time.max) if visibility_window_date else fields.Datetime.now()
        )
        incoming, outgoing, beyond_qty, beyond_date = op._explain_scheduled_moves(horizon_dt, horizon_dt)

        fmt = op._explain_fmt
        diagram = op._explain_diagram_geometry(
            order_forecast=order_forecast,
            gate_forecast=gate_forecast,
            min_qty=min_qty,
            max_qty=max_qty,
            target=target,
            below_min=below_min,
            total_delay=total_delay,
            visibility_days=int(visibility_days),
        )
        risks = op._get_replenishment_risks(
            below_min=below_min,
            gate_forecast=gate_forecast,
            order_forecast=order_forecast,
            min_qty=min_qty,
            max_qty=max_qty,
            rounded_to_order=rounded_to_order,
            raw_to_order=raw_to_order,
            no_vendor_delay=no_vendor_delay,
            visibility_days=visibility_days,
            global_visibility_days=global_visibility_days,
            beyond_qty=beyond_qty,
            beyond_date=beyond_date,
            visibility_window_date=visibility_window_date,
            rounding=rounding,
        )

        return {
            "orderpoint": op,
            "product_name": product.display_name,
            "location_name": op.location_id.display_name,
            "warehouse_name": op.warehouse_id.display_name,
            "uom_name": op.product_uom_name,
            "trigger": op.trigger,
            "has_rules": bool(op.rule_ids),
            "rule_names": ", ".join(op.rule_ids.mapped("name")),
            # quantities (formatted)
            "on_hand": fmt(on_hand),
            "incoming": fmt(incoming),
            "outgoing": fmt(outgoing),
            "in_progress": fmt(in_progress),
            "gate_forecast": fmt(gate_forecast),
            "order_forecast": fmt(order_forecast),
            "min_qty": fmt(min_qty),
            "max_qty": fmt(max_qty),
            "target": fmt(target),
            "raw_to_order": fmt(raw_to_order),
            "rounded_to_order": fmt(rounded_to_order),
            "qty_to_order": fmt(op.qty_to_order),
            "in_progress_zero": float_is_zero(in_progress, precision_rounding=rounding),
            "below_min": below_min,
            "is_manual_override": bool(op.qty_to_order_manual),
            "qty_multiple": op.qty_multiple,
            # lead time / horizon
            "total_delay": int(total_delay),
            "visibility_days": int(visibility_days),
            "global_visibility_days": global_visibility_days,
            "lead_days_date": format_date(op.env, lead_days_date) if lead_days_date else "",
            "visibility_window_date": format_date(op.env, visibility_window_date) if visibility_window_date else "",
            "today": format_date(op.env, fields.Date.today()),
            "delay_rows": delay_rows,
            # findings
            "risks": risks,
            # diagram geometry (SVG)
            "diagram": diagram,
        }

    def _explain_diagram_geometry(
        self,
        *,
        order_forecast,
        gate_forecast,
        min_qty,
        max_qty,
        target,
        below_min,
        total_delay,
        visibility_days,
    ):
        """Pure-arithmetic SVG geometry for the explanation diagram.

        Returns absolute coordinates (viewBox 0 0 480 150) for two strips:
        a quantity bar (forecast vs Min / Max-target, with the 'to order' gap)
        and a horizon timeline (today -> lead-time date -> visibility window).
        Coordinates target a wide viewBox (0 0 760 150) so the SVG can fill the
        dialog width instead of hugging the left. No field access / no
        ensure_one, so it is unit-testable on an empty recordset.
        """
        x0, x1 = 12.0, 748.0  # track left/right (room for a value label at the right)
        width = x1 - x0

        def r(v):
            return round(v, 1)

        # --- quantity bar ---
        axis_max = max(target, order_forecast, gate_forecast, max_qty, min_qty, 0.0) * 1.1 or 1.0
        scale = width / axis_max

        def qx(qty):
            # clamp inside the track; negative forecast renders at the left edge
            return r(x0 + min(max(qty, 0.0), axis_max) * scale)

        forecast_x = qx(order_forecast)
        target_x = qx(target)
        to_order_w = r(max(target_x - forecast_x, 0.0)) if below_min else 0.0

        # --- timeline ---
        day_max = float(total_delay + visibility_days) or 1.0
        tscale = width / day_max
        lead_x = r(x0 + total_delay * tscale)
        window_x = r(x0 + (total_delay + visibility_days) * tscale)

        return {
            "x0": x0,
            "x1": x1,
            "bar_y": 46.0,
            "bar_h": 26.0,
            "forecast_x": forecast_x,
            "forecast_w": r(forecast_x - x0),
            "to_order_x": forecast_x,
            "to_order_w": to_order_w,
            "min_x": qx(min_qty),
            "max_x": qx(max_qty),
            "gate_x": qx(gate_forecast),
            "below_min": below_min,
            "time_y": 116.0,
            "today_x": x0,
            "lead_x": lead_x,
            "window_x": window_x,
        }

    def _get_replenishment_risks(self, **kw):
        """Derive the 'where it may lose' findings from the reconstructed values.
        Each finding is a dict: {level: danger|warning|info|success, title, detail}."""
        self.ensure_one()
        op = self
        risks = []
        fmt = op._explain_fmt
        uom = op.product_uom_name

        if not op.rule_ids:
            risks.append(
                {
                    "level": "danger",
                    "title": _("No supply route / rule"),
                    "detail": _(
                        "No stock rule resolves for this product at this location, so nothing can be "
                        "procured even when stock is needed. Check the product's routes."
                    ),
                }
            )

        if kw["no_vendor_delay"]:
            risks.append(
                {
                    "level": "danger",
                    "title": _("No vendor found"),
                    "detail": _(
                        "No supplier is configured, so Odoo injects a %(days)s-day lead time. This pushes the "
                        "forecast date a year out and usually distorts the quantity. Set a vendor on the product.",
                        days=int(kw["no_vendor_delay"]),
                    ),
                }
            )

        # Demand scheduled beyond the visibility window is invisible to the order quantity.
        if not float_is_zero(kw["beyond_qty"], precision_rounding=kw["rounding"]):
            detail = _(
                "%(qty)s %(uom)s of demand is scheduled after the visibility window (%(date)s) and is NOT counted "
                "in the order quantity. If it falls due before a replenishment arrives, you can stock out. Raise "
                "Visibility Days (currently %(vis)s) on this rule, or the global Time Horizon (currently %(glob)s).",
                qty=fmt(kw["beyond_qty"]),
                uom=uom,
                date=format_date(op.env, kw["beyond_date"]) if kw["beyond_date"] else "",
                vis=kw["visibility_days"],
                glob=kw["global_visibility_days"],
            )
            risks.append(
                {"level": "warning", "title": _("Demand beyond the visibility window is invisible"), "detail": detail}
            )

        # Gate forecast at/above min -> no order, even though the visibility forecast is lower.
        if (
            not kw["below_min"]
            and float_compare(kw["order_forecast"], kw["min_qty"], precision_rounding=kw["rounding"]) < 0
        ):
            risks.append(
                {
                    "level": "warning",
                    "title": _("Order skipped by the lead-time gate"),
                    "detail": _(
                        "Forecast at lead time (%(gate)s) is at or above Min (%(min)s), so the rule orders nothing — "
                        "even though the forecast over the visibility window (%(order)s) is below Min. Demand sits "
                        "just beyond the lead-time date.",
                        gate=fmt(kw["gate_forecast"]),
                        min=fmt(kw["min_qty"]),
                        order=fmt(kw["order_forecast"]),
                    ),
                }
            )

        # Rounding to a quantity multiple inflated the quantity noticeably.
        if kw["below_min"] and op.qty_multiple:
            extra = kw["rounded_to_order"] - kw["raw_to_order"]
            if float_compare(extra, 0.0, precision_rounding=kw["rounding"]) > 0:
                risks.append(
                    {
                        "level": "info",
                        "title": _("Rounded up to a multiple"),
                        "detail": _(
                            "The raw need (%(raw)s) was rounded up to %(rounded)s to respect the quantity "
                            "multiple of %(multiple)s (+%(extra)s %(uom)s).",
                            raw=fmt(kw["raw_to_order"]),
                            rounded=fmt(kw["rounded_to_order"]),
                            multiple=op.qty_multiple,
                            extra=fmt(extra),
                            uom=uom,
                        ),
                    }
                )

        if op.qty_to_order_manual:
            risks.append(
                {
                    "level": "info",
                    "title": _("Manual quantity override"),
                    "detail": _(
                        "A manual To Order quantity (%(manual)s) is set, overriding the computed %(computed)s.",
                        manual=fmt(op.qty_to_order_manual),
                        computed=fmt(op.qty_to_order_computed),
                    ),
                }
            )

        if op.snoozed_until and op.snoozed_until > fields.Date.today():
            risks.append(
                {
                    "level": "info",
                    "title": _("Snoozed"),
                    "detail": _(
                        "This rule is snoozed until %(date)s and will be skipped until then.",
                        date=format_date(op.env, op.snoozed_until),
                    ),
                }
            )

        if not risks:
            risks.append(
                {
                    "level": "success",
                    "title": _("No visibility or horizon issues detected"),
                    "detail": _("The visibility window covers the scheduled demand and a supply route is available."),
                }
            )
        return risks
