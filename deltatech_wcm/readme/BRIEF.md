# BRIEF: World Class Manufacturing dashboard (deltatech_wcm)

Status: sections 1–8 implemented in 20.0.1.0.0; section 9 (unit production cost)
in 20.0.1.1.0. No open decisions.
Odoo target: 20.0. Suite: `deltatech` (branch `20.0`).

## 1. Scope

A single dashboard that groups the indicators of a plant under the ten
technical pillars of World Class Manufacturing (WCM):

1. Safety
2. Cost Deployment
3. Focused Improvement
4. Autonomous Maintenance
5. Planned Maintenance
6. Quality Control
7. Logistics and Customer Service
8. Early Equipment Management
9. People Development
10. Environment and Energy

For every pillar the dashboard shows its indicators, their target, the warning
threshold, the current value and a traffic light (green, yellow, red, or
"no data").

Indicators with a native source in Odoo are read from the existing modules.
Indicators for Safety and Focused Improvement (Kaizen) are placeholders until
the modules `modul-safety` and `modul-kaizen` exist in the monorepo. The module
has no dependency on them.

## 2. Users

- **Plant manager / WCM coordinator** (`mrp.group_mrp_manager`): sees the
  dashboard, edits targets and thresholds, enters manual values.
- **Shop floor / quality / maintenance users** (`mrp.group_mrp_user`): read the
  dashboard only.

## 3. Decisions taken

| # | Decision | Reason |
|---|----------|--------|
| D1 | Suite `deltatech`, module name `deltatech_wcm` | Custom manufacturing functionality lives in `deltatech` (see `deltatech_mrp`, `deltatech_mrp_concentration`). `deltatech_dashboard_builder` (suite `bitshop_ent`) is a generic KPI builder, but it sits in an e-commerce suite and depends on `deltatech_web_kpi_cards`. Depending on it would couple WCM to unrelated code. It stays a candidate for a later refactor, not a dependency now. |
| D2 | `depends`: `mrp`, `maintenance`, `quality`, `stock`; since 20.0.1.1.0 also `mrp_account` and `mrp_workorder` (see D13) | Each source comes from one of these modules. `quality` and `mrp_workorder` are Enterprise. The customers use Enterprise, so this is accepted. |
| D3 | Two models: `wcm.pillar` (the ten pillars, fixed data) and `wcm.indicator` (configurable target per indicator) | The targets are the configuration the client edits. Pillars do not change, so they are data records with `noupdate="1"`. |
| D4 | OEE availability is placed under **Planned Maintenance** | Availability is what planned maintenance protects. In this model OEE is a single indicator; it is not split into availability, performance and quality. |
| D5 | Pillar state = the worst state of its indicators (red > yellow > green); a pillar with no data is "no data" | The usual reading: one red indicator makes the pillar red. A pillar with no data does not look green by accident. |
| D6 | Default period for live sources: 30 days (`period_days` per indicator) | Short enough to react, long enough to avoid noise. OEE is the exception: the core `mrp.workcenter.oee` is computed over the last month by Odoo, and the module reads it as it is. |
| D7 | Placeholders for Safety and Focused Improvement are `manual` indicators | Without the modules, the only honest source is a value typed by the user. When the Safety/Kaizen modules exist, their indicators get a new source; `manual` indicators stay available. |
| D8 | Seed targets are **placeholders**, to be confirmed by the client | Real targets are client-specific. The seed values are a starting point, marked as such in the readme. |
| D9 | Multi-company: indicators carry `company_id`; live sources are computed per indicator company; `ir.access` restricts by `company_ids` | Consistent with the suite (`deltatech_mrp`). |
| D10 | Not in this module: snapshots history, alerts, email notifications, PDF reports, icon, banner, `i18n/ro.po` | Out of scope for the first version. Listed in section 7. |

## 4. Indicators (sources)

| Pillar | Indicator | Source | Direction | Target | Warning | Unit |
|--------|-----------|--------|-----------|--------|---------|------|
| Planned Maintenance | OEE availability | `mrp.workcenter.oee`, average of workcenters with data | higher | 85 | 70 | % |
| Planned Maintenance | MTBF | `maintenance.equipment.mtbf`, average of equipment with data | higher | 30 | 15 | days |
| Planned Maintenance | MTTR | `maintenance.equipment.mttr`, average of equipment with data | lower | 1 | 2 | days |
| Quality Control | Control failure rate | `quality.check` with `quality_state` in (pass, fail) and `control_date` in the period: failed / checked | lower | 2 | 5 | % |
| Quality Control | Scrap rate | `stock.move` with `is_scrap` and state done in the period / `mrp.production` done in the period (`product_qty`) | lower | 1 | 3 | % |
| Logistics and Customer Service | On-time deliveries | outgoing `stock.picking` done in the period: `date_done <= scheduled_date` / all done | higher | 95 | 85 | % |
| Safety | Lost-time injuries (LTI) | `manual` (placeholder until `modul-safety`) | lower | 0 | 1 | count |
| Focused Improvement | Kaizen projects closed on time | `manual` (placeholder until `modul-kaizen`) | higher | 80 | 50 | % |
| Autonomous Maintenance | 5S / TPM audits done on time | `manual` | higher | 90 | 70 | % |
| Cost Deployment | Deviation from the cost budget | `manual` | lower | 0 | 5 | % |
| Early Equipment Management | New equipment validated on time | `manual` | higher | 90 | 70 | % |
| People Development | Critical skills covered | `manual` (later: `hr_skills`) | higher | 80 | 60 | % |
| Environment and Energy | Waste recovered | `manual` | higher | 90 | 75 | % |

Pillars with no indicator yet (none in this version) show "no data".

## 5. Rules

- **State of an indicator**
  - no value → `none` (no data);
  - direction `higher`: value ≥ target → `green`; value ≥ warning → `yellow`; else `red`;
  - direction `lower`: value ≤ target → `green`; value ≤ warning → `yellow`; else `red`.
- **Consistency**: for `higher`, `warning ≤ target`; for `lower`, `warning ≥ target`.
  A violation raises a `ValidationError`.
- **Manual value**: `manual_value` is valid only together with `manual_date`; a
  manual indicator without a date has no data.
- **Pillar state**: worst state among its indicators; all `none` → `none`.
- **Live sources** return `none` when the base set is empty (no workcenter with
  productivity, no equipment with requests, no checks, no deliveries in the
  period, zero produced quantity for scrap rate).

## 6. Acceptance criteria

Each criterion is observable on the dashboard or in a test.

- **CA1**: after installation, the ten pillars exist, in the WCM order above, with
  the same names. Test: `test_seed_pillars`.
- **CA2**: after installation, the placeholder indicators exist and are
  `manual`; the module installs without Safety or Kaizen modules. Test:
  `test_placeholder_manual_indicators`.
- **CA3**: a `higher` indicator is green at or above target, yellow between
  warning and target, red below warning. Test: `test_state_higher`.
- **CA4**: a `lower` indicator is green at or below target, yellow between target
  and warning, red above warning. Test: `test_state_lower`.
- **CA5**: an indicator with no value shows "no data", not green or red. Test:
  `test_no_data_state`.
- **CA6**: a pillar shows the worst state of its indicators; all "no data" gives
  "no data". Test: `test_pillar_worst_state`.
- **CA7**: a `warning` that contradicts the direction is refused. Test:
  `test_warning_consistency`.
- **CA8**: a live source returns "no data" when the period has no data (partial
  coverage: the data path is tested only for the empty case in this version).
  Test: `test_live_sources_empty`.
- **CA9**: the dashboard lists the pillars with counters per state, and the
  indicators grouped by pillar. Checked on the Mentor fișă (screenshots), not by
  a unit test.
- **CA10**: a user without `mrp.group_mrp_manager` cannot change targets. Test:
  `test_access_user_read_only`.

## 7. Out of scope (possible later versions)

- Snapshot history per indicator (trend over time). Snapshots exist in
  `deltatech_dashboard_builder`; reuse can be discussed later.
- Alerts by email or chatter on state change.
- Split of OEE into availability, performance and quality.
- Live source from `modul-safety` and `modul-kaizen`: added when those modules
  exist, as a new `source` value.
- Live source for People Development from `hr_skills`.
- PDF report, icon, banner, `i18n/ro.po`.

## 8. Open points (presupuse, to confirm with the client)

- The target values in section 4 are placeholders. The client confirms them
  before go-live (D8).
- OEE is read as Odoo computes it (last month, all workcenters with productivity).

## 9. Unit production cost and cost of losses (requested and confirmed 2026-11-17)

### 9.1 Need

Reference formula:

    unit cost = (materials + labour + shop overhead) / good quantity

For each loss (scrap, stoppages, changeovers, energy, waste) the module shows
how many lei per unit it costs. The difference between the standard and the
actual cost shows the losses per product. The saving of an improvement project
is computed by the Kaizen module from the cost of the loss (D12).

### 9.2 Overlap found

- The core **MO Overview** report (`mrp`, with the `mrp_account` and
  `mrp_workorder` overrides) already computes the real cost of a manufacturing
  order: consumed components + operations (work center and employee hourly
  cost) + BoM `extra_cost`. The module reads it (`mo_cost`); it does not compute
  the real cost a second time.
- The core **BoM Structure** report (`mrp`, with the `mrp_account` override)
  computes the standard cost from the BoM (`bom_cost`), including `extra_cost`.
  The module reads it.

### 9.3 Sources

| Element | Standard | Actual |
|---------|----------|--------|
| Materials, labour, shop overhead | BoM Structure report, `bom_cost` for the good quantity | MO Overview report, `mo_cost`, plus the value of scrapped components |
| Energy, waste | — (only through BoM `extra_cost`, if the client uses it) | manual cost per period and work center (`wcm.cost.manual`), spread over the good units (D11) |
| Good quantity | — | produced quantity − scrapped quantity of the finished product |

| Loss | Source | Cost |
|------|--------|------|
| Scrap | scrapped moves of the order (`stock.move.is_scrap`, components and finished product) | value of the scrapped components + scrapped finished units × actual cost per produced unit |
| Stoppages | productivity log of the order's work orders, category Availability, except the reason "Setup and Adjustments" | hours × (`costs_hour` + employee hourly cost of the log) |
| Changeovers | productivity log, reason "Setup and Adjustments" (`mrp.block_reason2`) | same formula |
| Energy | `wcm.cost.manual`, type energy | amount prorated to the period, spread over the good units of the work center |
| Waste | `wcm.cost.manual`, type waste | same |

The cost per unit of each loss = cost of the loss / good quantity.

Stoppage and changeover hours are the durations Odoo stores on the
productivity log: for availability losses, Odoo counts only the working hours
of the work center calendar.

### 9.4 Decisions (confirmed 2026-11-17)

| # | Decision |
|---|----------|
| D10 | (O1 a) One dashboard indicator on Cost Deployment: "Unit cost deviation (actual vs standard)" in %, weighted by the good quantity of the period: (Σ actual − Σ standard) / Σ standard × 100. A separate list (`wcm.cost.line`) shows, per product and period, the standard and actual unit cost and the lei per unit of each loss. |
| D11 | (O2 a) Energy and waste are entered manually as a cost per period and work center (`wcm.cost.manual`). The amount is prorated to the days that overlap the analysed period, then spread over the good units of the done orders that used that work center, in proportion to their good quantity. It is added to the actual cost. |
| D12 | (O3 a) `deltatech_wcm` exposes the cost of each loss (`wcm.cost.line`, and `wcm.cost.line._get_loss_costs(company, date_from, date_to, product=None)`); the Kaizen module computes the saving (cost of the loss × expected reduction). WCM does not depend on Kaizen. |
| D13 | (O4 a) `depends` adds `mrp_account` (BoM `extra_cost`, move value) and `mrp_workorder` (employee hourly cost on the productivity log). |
| D14 | (presupus) The cost list is rebuilt on demand (button "Recompute" on the list, last `period_days` days, default 30), not by a scheduled job. The dashboard indicator is computed live. |

### 9.5 Acceptance criteria

- **CA11**: for a done manufacturing order without scrap and without manual
  costs, the actual unit cost in the cost list equals the unit cost of the MO
  Overview report. Test: `test_actual_unit_cost_matches_mo_overview`.
- **CA12**: the standard unit cost comes from the BoM Structure report; the
  deviation actual vs standard appears per product in lei per unit and in %.
  Test: `test_standard_cost_and_deviation`.
- **CA13**: stoppages and changeovers logged on the order's work orders appear
  in the cost list in lei per unit (hours × hourly cost / good quantity), next
  to the deviation. Test: `test_stoppage_and_changeover_cost`. Scrap: partial
  coverage (computed, no test with a scrapped move in this version).
- **CA14**: the Cost Deployment pillar has the indicator "Unit cost deviation"
  with target and traffic light; with no done order in the period it shows no
  data. Test: `test_cost_deviation_indicator`.
- **CA15**: a manual energy or waste cost on a work center is spread over the
  good units of the period and added to the actual cost. Test:
  `test_manual_energy_cost_allocation`.
- **CA16**: the cost of each loss is available to other modules through
  `_get_loss_costs`; the saving itself is out of scope here (Kaizen). Test:
  `test_get_loss_costs`.
