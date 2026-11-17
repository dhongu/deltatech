# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

# Totals collected for each product. The cost of each loss is in lei for the period.
COST_KEYS = (
    "production_count",
    "good_qty",
    "standard_cost",
    "actual_cost",
    "scrap_cost",
    "stoppage_cost",
    "changeover_cost",
    "energy_cost",
    "waste_cost",
)
LOSS_KEYS = ("scrap", "stoppage", "changeover", "energy", "waste")


class WcmCostLine(models.Model):
    _name = "wcm.cost.line"
    _description = "WCM Unit Cost per Product"
    _order = "date_to desc, deviation_pct desc, id"

    date_from = fields.Date(required=True, readonly=True)
    date_to = fields.Date(required=True, readonly=True)
    company_id = fields.Many2one("res.company", required=True, readonly=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    product_id = fields.Many2one("product.product", required=True, readonly=True, index=True)
    production_count = fields.Integer("Orders", readonly=True)
    good_qty = fields.Float("Good quantity", digits="Product Unit", readonly=True)
    standard_cost = fields.Monetary(readonly=True)
    actual_cost = fields.Monetary(readonly=True)
    scrap_cost = fields.Monetary(readonly=True)
    stoppage_cost = fields.Monetary(readonly=True)
    changeover_cost = fields.Monetary(readonly=True)
    energy_cost = fields.Monetary(readonly=True)
    waste_cost = fields.Monetary(readonly=True)

    standard_unit_cost = fields.Monetary(compute="_compute_unit_costs", store=True)
    actual_unit_cost = fields.Monetary(compute="_compute_unit_costs", store=True)
    deviation_unit = fields.Monetary("Deviation per unit", compute="_compute_unit_costs", store=True)
    deviation_pct = fields.Float("Deviation (%)", digits=(16, 2), compute="_compute_unit_costs", store=True)
    scrap_unit = fields.Monetary("Scrap / unit", compute="_compute_unit_costs", store=True)
    stoppage_unit = fields.Monetary("Stoppages / unit", compute="_compute_unit_costs", store=True)
    changeover_unit = fields.Monetary("Changeovers / unit", compute="_compute_unit_costs", store=True)
    energy_unit = fields.Monetary("Energy / unit", compute="_compute_unit_costs", store=True)
    waste_unit = fields.Monetary("Waste / unit", compute="_compute_unit_costs", store=True)
    loss_unit = fields.Monetary("Losses / unit", compute="_compute_unit_costs", store=True)

    @api.depends("good_qty", "standard_cost", "actual_cost", *(f"{loss}_cost" for loss in LOSS_KEYS))
    def _compute_unit_costs(self):
        for line in self:
            qty = line.good_qty or 0.0
            for loss in LOSS_KEYS:
                line[f"{loss}_unit"] = line[f"{loss}_cost"] / qty if qty else 0.0
            line.loss_unit = sum(line[f"{loss}_unit"] for loss in LOSS_KEYS)
            line.standard_unit_cost = line.standard_cost / qty if qty else 0.0
            line.actual_unit_cost = line.actual_cost / qty if qty else 0.0
            line.deviation_unit = line.actual_unit_cost - line.standard_unit_cost
            line.deviation_pct = (
                (line.actual_cost - line.standard_cost) * 100.0 / line.standard_cost if line.standard_cost else 0.0
            )

    # ------------------------------------------------------------------
    # Rebuild of the list
    # ------------------------------------------------------------------

    @api.model
    def action_refresh(self, period_days=30):
        """Rebuild the list for the last ``period_days`` days, for the selected companies."""
        date_to = fields.Datetime.now()
        date_from = date_to - relativedelta(days=period_days)
        for company in self.env.companies:
            self._refresh(company, date_from, date_to)
        return {"type": "ir.actions.client", "tag": "soft_reload"}

    @api.model
    def _refresh(self, company, date_from, date_to):
        self.search([("company_id", "=", company.id)]).unlink()
        data = self._compute_cost_data(company, date_from, date_to)
        return self.create(
            [
                {
                    "company_id": company.id,
                    "product_id": product.id,
                    "date_from": date_from.date(),
                    "date_to": date_to.date(),
                    **totals,
                }
                for product, totals in data.items()
            ]
        )

    # ------------------------------------------------------------------
    # Computation (also used live by the dashboard indicator and by Kaizen)
    # ------------------------------------------------------------------

    @api.model
    def _compute_cost_data(self, company, date_from, date_to):
        """Return {product: totals} for the orders done in [date_from, date_to] (datetimes)."""
        productions = self.env["mrp.production"].search(
            [
                ("company_id", "=", company.id),
                ("state", "=", "done"),
                ("date_finished", ">=", date_from),
                ("date_finished", "<=", date_to),
            ]
        )
        per_production = {}
        for production in productions:
            costs = self._get_production_costs(production)
            if costs:
                per_production[production] = costs
        self._allocate_manual_costs(company, date_from.date(), date_to.date(), per_production)
        result = defaultdict(lambda: dict.fromkeys(COST_KEYS, 0.0))
        for production, costs in per_production.items():
            totals = result[production.product_id]
            for key in COST_KEYS:
                totals[key] += costs[key]
        return dict(result)

    @api.model
    def _get_loss_costs(self, company, date_from, date_to, product=None):
        """Cost of each loss for the period: {loss: {"amount": lei, "per_unit": lei per good unit}}.

        Entry point for other modules (the Kaizen module computes the saving from it).
        """
        data = self._compute_cost_data(company, date_from, date_to)
        if product:
            data = {key: value for key, value in data.items() if key in product}
        good_qty = sum(totals["good_qty"] for totals in data.values())
        result = {}
        for loss in LOSS_KEYS:
            amount = sum(totals[f"{loss}_cost"] for totals in data.values())
            result[loss] = {"amount": amount, "per_unit": amount / good_qty if good_qty else 0.0}
        return result

    @api.model
    def _get_production_costs(self, production):
        """Costs of one done order. None when the order has no good quantity."""
        produced = production.qty_produced
        scrap_moves = self.env["stock.move"].search(
            [
                ("is_scrap", "=", True),
                ("state", "=", "done"),
                "|",
                ("production_id", "=", production.id),
                ("raw_material_production_id", "=", production.id),
            ]
        )
        finished_scrap = scrap_moves.filtered(lambda move: move.product_id == production.product_id)
        scrapped_qty = sum(finished_scrap.mapped("product_qty"))
        good_qty = produced - scrapped_qty
        if good_qty <= 0:
            return None

        # Real cost as the MO Overview report computes it (components, operations, extra cost).
        report = self.env["report.mrp.report_mo_overview"]._get_report_data(production.id)
        mo_cost = report["summary"]["mo_cost"]
        component_scrap_value = sum(abs(value) for value in (scrap_moves - finished_scrap).mapped("value"))
        scrap_cost = component_scrap_value + (scrapped_qty * mo_cost / produced if produced else 0.0)
        stoppage_cost, changeover_cost = self._get_time_loss_costs(production)
        return {
            "production_count": 1,
            "good_qty": good_qty,
            "standard_cost": self._get_standard_cost(production, good_qty),
            "actual_cost": mo_cost + component_scrap_value,
            "scrap_cost": scrap_cost,
            "stoppage_cost": stoppage_cost,
            "changeover_cost": changeover_cost,
            "energy_cost": 0.0,
            "waste_cost": 0.0,
        }

    @api.model
    def _get_standard_cost(self, production, good_qty):
        """Standard cost of the good quantity, as the BoM Structure report computes it."""
        if not production.bom_id:
            return 0.0
        bom = production.bom_id
        quantity = production.uom_id._compute_quantity(good_qty, bom.uom_id)
        data = self.env["report.mrp.report_bom_structure"]._get_bom_data(
            bom, production.warehouse_id, production.product_id, line_qty=quantity, ignore_stock=True
        )
        return data["bom_cost"]

    @api.model
    def _get_time_loss_costs(self, production):
        """Cost of the stoppages and of the changeovers logged on the order's work orders."""
        if not production.workorder_ids:
            return 0.0, 0.0
        setup_reason = self.env.ref("mrp.block_reason2", raise_if_not_found=False)
        logs = self.env["mrp.workcenter.productivity"].search(
            [
                ("workorder_id", "in", production.workorder_ids.ids),
                ("loss_id.loss_type", "=", "availability"),
                ("date_end", "!=", False),
            ]
        )
        stoppage = changeover = 0.0
        for log in logs:
            cost = log.duration / 60.0 * (log.workcenter_id.costs_hour + log.employee_cost)
            if setup_reason and log.loss_id == setup_reason:
                changeover += cost
            else:
                stoppage += cost
        return stoppage, changeover

    @api.model
    def _allocate_manual_costs(self, company, date_from, date_to, per_production):
        """Spread the manual energy and waste costs over the good units of each work center."""
        manual_costs = self.env["wcm.cost.manual"].search(
            [
                ("company_id", "=", company.id),
                ("date_from", "<=", date_to),
                ("date_to", ">=", date_from),
            ]
        )
        for manual in manual_costs:
            amount = manual._get_amount_for_period(date_from, date_to)
            productions = [
                production
                for production in per_production
                if manual.workcenter_id in production.workorder_ids.workcenter_id
            ]
            good_total = sum(per_production[production]["good_qty"] for production in productions)
            if not amount or not good_total:
                continue
            for production in productions:
                share = amount * per_production[production]["good_qty"] / good_total
                per_production[production][f"{manual.cost_type}_cost"] += share
                per_production[production]["actual_cost"] += share
