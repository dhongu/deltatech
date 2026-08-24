from datetime import datetime, time

from odoo import _, fields, models
from odoo.tools import float_compare, float_is_zero, format_date

# Move states that still represent an open (not yet done/cancelled) flow, the
# same set Odoo uses when computing the forecast / deadline on an orderpoint.
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

    def _explain_scheduled_moves(self, horizon_dt):
        """Return (incoming, outgoing, beyond_qty, beyond_date) open moves for
        this orderpoint's product/location: receipts and demand up to the lead
        horizon, plus any demand scheduled *after* it (invisible to the forecast)."""
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
        beyond = Move.search(common + [("location_id", "child_of", loc.id), ("date", ">", horizon_dt)], order="date")
        beyond_qty = sum(beyond.mapped("product_qty"))
        beyond_date = beyond[:1].date
        return incoming, outgoing, beyond_qty, beyond_date

    def _get_replenishment_explanation(self):
        """Reconstruct, with live numbers, the computation Odoo runs on this
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
        horizon_time = delays.get("horizon_time", 0.0)
        no_vendor_delay = delays.get("no_vendor_found_delay", 0.0)
        horizon_days = op.get_horizon_days()
        horizon_from_context = "global_horizon_days" in op.env.context
        lead_horizon_date = op.lead_horizon_date

        # Keep only the readable rows of the delay breakdown (label, "+ N day(s)")
        delay_rows = [(label, value) for label, value in description if isinstance(value, str)]

        # --- Quantities (mirror _compute_qty / _get_qty_to_order) ---
        on_hand = op.qty_on_hand
        in_progress = op._quantity_in_progress().get(op.id, 0.0)
        product_ctx = op._get_product_context()
        virtual_at_horizon = product.with_context(product_ctx).read(["virtual_available"])[0]["virtual_available"]
        forecast = op.qty_forecast  # == virtual_at_horizon + in_progress
        min_qty = op.product_min_qty
        max_qty = op.product_max_qty
        target = max(min_qty, max_qty)

        # --- Decision + order quantity math (mirror _get_qty_to_order) ---
        below_min = float_compare(forecast, min_qty, precision_rounding=rounding) < 0
        raw_to_order = (target - forecast) if below_min else 0.0
        rounded_to_order = op._get_multiple_rounded_qty(raw_to_order) if below_min else 0.0
        multiple = op.replenishment_uom_id or op._get_replenishment_multiple_alternative(raw_to_order)
        # `qty_multiple` is a legacy rounding field added by deltatech_stock_orderpoint_multiple
        # (not a hard dependency): getattr keeps this module working without it installed.
        legacy_qty_multiple = getattr(op, "qty_multiple", 0.0)
        if multiple:
            multiple_name = multiple.display_name
        elif legacy_qty_multiple:
            multiple_name = f"{op._explain_fmt(legacy_qty_multiple)} {op.product_uom_name}"
        else:
            multiple_name = ""

        # --- Scheduled moves for the breakdown + beyond-horizon visibility ---
        horizon_dt = datetime.combine(lead_horizon_date, time.max) if lead_horizon_date else fields.Datetime.now()
        incoming, outgoing, beyond_qty, beyond_date = op._explain_scheduled_moves(horizon_dt)

        fmt = op._explain_fmt
        diagram = op._explain_diagram_geometry(
            forecast=forecast,
            min_qty=min_qty,
            max_qty=max_qty,
            target=target,
            below_min=below_min,
            total_delay=total_delay,
            horizon_days=int(horizon_days),
        )
        risks = op._get_replenishment_risks(
            below_min=below_min,
            forecast=forecast,
            min_qty=min_qty,
            max_qty=max_qty,
            rounded_to_order=rounded_to_order,
            raw_to_order=raw_to_order,
            no_vendor_delay=no_vendor_delay,
            horizon_days=horizon_days,
            beyond_qty=beyond_qty,
            beyond_date=beyond_date,
            lead_horizon_date=lead_horizon_date,
            multiple_name=multiple_name,
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
            "virtual_at_horizon": fmt(virtual_at_horizon),
            "forecast": fmt(forecast),
            "min_qty": fmt(min_qty),
            "max_qty": fmt(max_qty),
            "target": fmt(target),
            "raw_to_order": fmt(raw_to_order),
            "rounded_to_order": fmt(rounded_to_order),
            "qty_to_order": fmt(op.qty_to_order),
            "in_progress_zero": float_is_zero(in_progress, precision_rounding=rounding),
            "below_min": below_min,
            "is_manual_override": bool(op.qty_to_order_manual),
            "multiple_name": multiple_name,
            # lead time / horizon
            "total_delay": int(total_delay),
            "horizon_time": int(horizon_time),
            "horizon_days": int(horizon_days),
            "horizon_from_context": horizon_from_context,
            "lead_horizon_date": format_date(op.env, lead_horizon_date) if lead_horizon_date else "",
            "today": format_date(op.env, fields.Date.today()),
            "deadline_date": format_date(op.env, op.deadline_date) if op.deadline_date else "",
            "delay_rows": delay_rows,
            # findings
            "risks": risks,
            # diagram geometry (SVG)
            "diagram": diagram,
        }

    def _explain_diagram_geometry(
        self,
        *,
        forecast,
        min_qty,
        max_qty,
        target,
        below_min,
        total_delay,
        horizon_days,
    ):
        """Pure-arithmetic SVG geometry for the explanation diagram.

        Returns absolute coordinates (viewBox 0 0 384 150) for two strips:
        a quantity bar (forecast vs Min / Max-target, with the 'to order' gap)
        and a horizon timeline (today -> lead-time -> lead horizon date).
        Coordinates target a wide viewBox (0 0 760 150) so the SVG can fill the
        dialog width instead of hugging the left. No field access / no
        ensure_one, so it is unit-testable on an empty recordset.
        """
        x0, x1 = 12.0, 748.0
        width = x1 - x0

        def r(v):
            return round(v, 1)

        # --- quantity bar ---
        axis_max = max(target, forecast, max_qty, min_qty, 0.0) * 1.1 or 1.0
        scale = width / axis_max

        def qx(qty):
            return r(x0 + min(max(qty, 0.0), axis_max) * scale)

        forecast_x = qx(forecast)
        target_x = qx(target)
        to_order_w = r(max(target_x - forecast_x, 0.0)) if below_min else 0.0

        # --- timeline: today -> lead-time boundary -> lead horizon ---
        day_max = float(total_delay + horizon_days) or 1.0
        tscale = width / day_max
        lead_x = r(x0 + total_delay * tscale)
        horizon_x = r(x0 + (total_delay + horizon_days) * tscale)

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
            "below_min": below_min,
            "time_y": 116.0,
            "today_x": x0,
            "lead_x": lead_x,
            "horizon_x": horizon_x,
        }

    def _get_replenishment_risks(self, **kw):
        """Derive the 'where it may lose' findings from the reconstructed values.
        Each finding is a dict: {level: danger|warning|info, title, detail}."""
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
                        "forecast horizon a year out and usually distorts the quantity. Set a vendor on the product.",
                        days=int(kw["no_vendor_delay"]),
                    ),
                }
            )

        # Demand scheduled beyond the lead horizon is invisible to the forecast.
        if not float_is_zero(kw["beyond_qty"], precision_rounding=kw["rounding"]):
            detail = _(
                "%(qty)s %(uom)s of demand is scheduled after the lead horizon (%(date)s) and is NOT counted "
                "in the forecast. If it falls due before a replenishment arrives, you can stock out. Increase the "
                "Replenishment Horizon (currently %(horizon)s days) to make it visible.",
                qty=fmt(kw["beyond_qty"]),
                uom=uom,
                date=format_date(op.env, kw["beyond_date"]) if kw["beyond_date"] else "",
                horizon=kw["horizon_days"],
            )
            risks.append({"level": "warning", "title": _("Demand beyond the horizon is invisible"), "detail": detail})

        # Forecast at/above min -> no order, but a deadline says a stockout is coming anyway.
        if not kw["below_min"] and op.deadline_date:
            risks.append(
                {
                    "level": "warning",
                    "title": _("Potential stockout despite no order"),
                    "detail": _(
                        "Forecast (%(forecast)s) is at or above Min (%(min)s), so nothing is ordered — but a "
                        "deadline of %(deadline)s was found. A future arrival is likely expected only after stock "
                        "dips below Min. Check the Forecast Report.",
                        forecast=fmt(kw["forecast"]),
                        min=fmt(kw["min_qty"]),
                        deadline=format_date(op.env, op.deadline_date),
                    ),
                }
            )

        # Rounding to a packaging/UoM multiple (native or legacy qty_multiple)
        # inflated the quantity noticeably.
        if kw["below_min"] and kw["multiple_name"]:
            extra = kw["rounded_to_order"] - kw["raw_to_order"]
            if float_compare(extra, 0.0, precision_rounding=kw["rounding"]) > 0:
                risks.append(
                    {
                        "level": "info",
                        "title": _("Rounded up to a multiple"),
                        "detail": _(
                            "The raw need (%(raw)s) was rounded up to %(rounded)s to respect the multiple "
                            "'%(multiple)s' (+%(extra)s %(uom)s).",
                            raw=fmt(kw["raw_to_order"]),
                            rounded=fmt(kw["rounded_to_order"]),
                            multiple=kw["multiple_name"],
                            extra=fmt(extra),
                            uom=uom,
                        ),
                    }
                )

        # Manual override hides the computed number.
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

        # Snoozed manual orderpoint won't run with the scheduler.
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
                    "detail": _("The forecast window covers the scheduled demand and a supply route is available."),
                }
            )
        return risks
