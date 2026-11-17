# BRIEF: World Class Manufacturing dashboard (deltatech_wcm)

Status: sections 1–8 implemented (20.0.1.0.0). Section 9 (unit production cost)
added on 2026-11-17: open decisions O1–O4, not implemented yet.
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
| D2 | `depends`: `mrp`, `maintenance`, `quality`, `stock` | Each source comes from one of these modules. `quality` is Enterprise (OEEL-1). The customers use Enterprise, so this is accepted. Nothing else is needed. |
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

## 9. Unit production cost and cost of losses (requested 2026-11-17)

Status: **open**. Implementation starts only after O1–O4 are answered.

### 9.1 Need

Reference formula:

    unit cost = (materials + labour + shop overhead) / good quantity

The dashboard shows, for each loss (scrap, stoppages, changeovers, energy,
waste), how many lei per unit it costs, and how much an improvement project
would save. This links the Cost Deployment pillar with the Kaizen module.

The difference between the standard cost and the actual cost shows the losses
per product.

### 9.2 Overlap found

- The core **MO Overview** report (`mrp`, `mrp.report_mo_overview`) already
  computes, per manufacturing order, the expected cost (from the BoM) and the
  real cost (consumed components + operations), and the unit cost
  (`unit_mo_cost`). The module reuses this logic; it does not compute costs a
  second time.
- `mrp_account` already values a finished product as consumed components +
  work center cost (`costs_hour` × time) + `extra_cost` per unit from the BoM
  (its help text: "labour, energy, packaging").
- `mrp_workorder` (Enterprise) adds the employee cost to the operation cost.

### 9.3 Sources (proposal)

| Element | Standard | Actual |
|---------|----------|--------|
| Materials | BoM components × `standard_price` | value of the consumed component moves |
| Labour | `duration_expected` × employee cost | `duration` × employee cost (`mrp_workorder`) |
| Shop overhead | `duration_expected` × `costs_hour` + BoM `extra_cost` | `duration` × `costs_hour` + BoM `extra_cost` |
| Good quantity | — | produced quantity − scrapped quantity − quantity of failed quality checks |

| Loss | Native source | Lei per unit |
|------|---------------|--------------|
| Scrap | scrapped moves (`stock.move.is_scrap`) and failed `quality.check` | value of the scrap / good quantity |
| Stoppages | productivity log, category Availability (except "Setup and Adjustments") | blocked time × (`costs_hour` + labour) / good quantity |
| Changeovers | productivity log, reason "Setup and Adjustments" | same formula, only this reason |
| Energy | none in Odoo | see O2 |
| Waste | none in Odoo | see O2 |

### 9.4 Open decisions

- **O1. Level of detail.** (a, recommended) The dashboard keeps one indicator
  per pillar row: on Cost Deployment, "actual vs standard unit cost deviation
  (%)", weighted by the good quantity of the period; a separate list shows lei
  per unit per product and per loss. (b) One dashboard indicator per product.
  (c) Only the company total in lei.
- **O2. Energy and waste.** Odoo has no source. (a, recommended) A manual cost
  per period and work center, spread over the good units of that work center.
  (b) Left out until a dedicated module exists. (c) Read from the BoM
  `extra_cost` only.
- **O3. Savings of an improvement project.** (a, recommended) `deltatech_wcm`
  exposes the cost of each loss (lei per unit and per period); the Kaizen
  module computes the saving (cost of the loss × expected reduction %), so
  WCM does not depend on Kaizen. (b) WCM holds the expected reduction itself
  and computes the saving.
- **O4. Dependencies.** Labour cost per employee and `extra_cost` need
  `mrp_workorder` (Enterprise) and `mrp_account`. (a, recommended) Add both to
  `depends`. (b) Only `mrp_account`: labour is in `costs_hour`, without the
  employee cost.

### 9.5 Acceptance criteria (draft, finalised after O1–O4)

- **CA11**: for a done manufacturing order, the actual unit cost equals
  (materials + labour + shop overhead) / good quantity, and matches the unit
  cost of the MO Overview report.
- **CA12**: the standard unit cost comes from the BoM; the deviation actual vs
  standard appears per product, in lei per unit and in %.
- **CA13**: for each loss with a native source (scrap, stoppages, changeovers),
  the list shows lei per unit for the period; the sum of the losses and the
  deviation are shown side by side.
- **CA14**: the Cost Deployment pillar has the indicator "unit cost deviation"
  with target and traffic light, like the other indicators.
- **CA15**: energy and waste follow the answer to O2.
- **CA16**: the saving of an improvement project follows the answer to O3.
