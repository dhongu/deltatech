# Brief: deltatech_safety_register

Language: English (the `deltatech` suite's readme fragments are in English), section titles included.
Discussion with the user stays in Romanian.

## Request

"Modul nou de registru Safety (incidente, accidente de muncă, near miss) pentru Odoo 20", 2026-11-17.
Scope from the originating session: register incidents, work accidents and near misses; classify
them; record root cause; corrective actions with owner and deadline; indicators (LTIFR, number of
near misses, days without accident).

## Scope

Companies that run World Class Manufacturing programmes have no place in Odoo to record safety
events. Today they keep them in spreadsheets, so the indicators (LTIFR, near misses, days without
accident) are computed by hand and corrective actions are not followed up. The module gives one
register per company, a classification of each event, root cause, corrective actions with an owner
and a deadline, and the indicators for a chosen year.

## Who operates

- **Safety officer** (group `deltatech_safety_register.group_safety_officer`): creates and edits
  events and actions, reads the indicators.
- **Safety manager** (group `deltatech_safety_register.group_safety_manager`, implies officer):
  additionally edits closed events and deletes events still in state Reported.
- Other users: no access.

## Scope of fit

- Suite: **deltatech**. Reason: business modules owned by Terrabit that are not localisation and not
  IAP/branded (`deltatech_mrp`, `deltatech_business_process`, `deltatech_expenses_hr_expense`
  already live here). `terrabit` holds branded/IAP modules and `l10n_ro_*` is accounting
  localisation, so neither fits. No suite has an HSE or safety module (search of odoo-addons,
  enterprise and odoo core: no match for safety/incident/accident register).
- Module: new, not an extension. Overlaps checked:
  - `maintenance` (core): equipment and requests. Different entity; a safety event may reference
    equipment in v2, not in v1.
  - `quality` (enterprise): `quality.alert` is product non-conformity. Using it would add an
    enterprise dependency to a community-level module, and its model does not hold injury data.
  - `hr` and `hr_attendance` (core): employees, departments and worked hours. Used as Many2one
    targets and as the hours source; no fields added to them.

## Depends

- `base`: core.
- `mail`: chatter on events and corrective actions, and `mail.activity` for action deadlines.
- `hr`: the injured person is an employee; department is copied from the employee.
- `hr_attendance`: hours worked for LTIFR come from `hr.attendance.worked_hours` (decision D1).

Not depended on: `mrp` (the register works without work centres), `maintenance`, `quality`.

## Models

- `deltatech.safety.event`: one incident, accident or near miss. Fields: name (sequence
  `SAF/YYYY/NNNN`), company_id, event_type, date, location (char), is_commute (boolean, accident de
  traseu), employee_id, partner_id (non-employee injured person, optional), injured_name (char, for a
  non-employee without partner), department_id (computed from employee), description, root_cause
  (text), state (`reported` → `closed`), closed_date, action_ids, open_action_count (computed).
- `deltatech.safety.action`: corrective action. Fields: event_id, description, user_id
  (responsible), deadline (date), state (`open` / `done`), done_date.
- Indicators: a transient model `deltatech.safety.indicator` (in `wizard/`), filtered by company and
  year, with computed LTIFR, near miss count, lost-time count, hours worked and days without
  accident. No separate hours model: hours come from attendance.

Standard models extended: none.

## Flow

1. Safety officer opens Safety → Events → New, picks an event type, date, location and description.
2. If type is an injury, selects the injured person (employee, or partner, or a name). Ticks
   "accident de traseu" if it happened on the way to or from work.
3. Saves → event is `reported`, reference assigned.
4. Enters the root cause, then adds corrective actions (description, responsible, deadline). Each
   action creates a `mail.activity` for its responsible user on the event.
5. Marks actions done; when no action is open, Close is available.
6. Closing sets `closed_date` and locks the event for officers (managers may still edit).
7. Safety → Reporting → Indicators, pick a year and company: LTIFR, near miss count, lost-time
   count, hours worked, days without accident. Export the event list to XLSX from the list view.

## Acceptance criteria

- **CA1:** Given no events, when an officer creates a near miss with date and description and saves,
  then the state is `Reported` and the reference is `SAF/<year of the event date>/NNNN` (next number on
  the next event).
- **CA2:** Given an event of an injury type (`Injury`, `Lost-time injury` or `Fatal`), when saved with
  no injured person (employee, partner or name), then saving fails with a message naming the three
  fields. With any of the three set, it saves.
- **CA3:** Given an open event, when an action is added with a responsible user and a deadline,
  then the responsible user receives one open `mail.activity` on the event with that deadline.
- **CA4:** Given an event with one open action, when the officer presses Close, then nothing
  changes and a message says actions must be done first. After marking the action done, Close
  sets state `Closed` and `closed_date` to today.
- **CA5:** Given company A has `hr.attendance` records worth 160 hours in January 2026 and 2 lost-time
  injuries with 5 near misses in 2026, when indicators are opened for company A and 2026 with hours
  for all 12 months summing to 400 000, then LTIFR = 2 × 1 000 000 / 400 000 = 5.00 and near miss
  count = 5 and hours worked = 400 000.
- **CA6:** Given the same company and year but no attendance records for March 2026, when the
  indicators are opened, then LTIFR is hidden and a warning lists the month as `03/2026`. Only months that have started are
  checked, so the current year's future months do not block LTIFR.
- **CA7:** Given injury events on 2026-03-02 and 2026-05-10 and no later injury, when indicators
  are opened on 2026-05-20, then days without accident = 10. Near misses and incidents do not
  count as injuries. With no injury at all, the field is empty and labelled "no injury recorded".
- **CA8:** Given a user who is not in either safety group, when they open events, then they get no
  access. Given a user of company B, when they open events of company A, then they see none.
- **CA9:** Given an officer and an event in state `Closed`, when they try to edit the description,
  then the save is refused. A manager can edit it.
- **CA10:** Given events with `is_commute` ticked and the rest not, when the indicators are opened,
  then the LTIFR counts only events with `is_commute` = False; the commute count is shown on its own.
- **CA11:** Given the event list of a company, when the user exports to XLSX, then the file contains
  one row per event with reference, date, type, injured person, commute flag, state and open actions.

## Edge cases

- Multi-company: every model carries company_id; access uses `ir.access` domains on
  `company_ids`. Indicators are per company; no consolidation in v1.
- Event deleted while actions exist: only in state `Reported`, deletion also removes its actions;
  closed events cannot be deleted by anyone.
- Action deadline in the past at creation: allowed, but the activity is created as due today.
- Same employee with two injury events on the same day: allowed; counted twice in lost-time count.
- Repeated Close click: second press is a no-op.
- Hours: a month with attendance records summing to zero counts as missing, not as zero.
- Employees without attendance (e.g. contractors): their hours are not in the hours base. Stated in
  the indicator help text.

## Decisions taken

| Decision | Chosen | Reason |
|---|---|---|
| Suite | `deltatech` | See "Scope of fit" |
| Technical name | `deltatech_safety_register` | Suite prefix plus the subject |
| Event reference | sequence `SAF/YYYY/NNNN` with the year of the event date, one sequence for all companies | A per-company sequence would need company-specific sequence records; v1 keeps one |
| Event types | `near_miss`, `incident` (no injury), `injury` (no time lost), `lost_time_injury`, `fatal` | Covers the classes that feed near-miss and lost-time counts. Labels may change without code change |
| LTIFR | lost-time count × 1 000 000 / hours worked, lost-time = `lost_time_injury` + `fatal` and `is_commute` = False | Standard definition per million hours worked; client to confirm with the field list |
| Days without accident | days since the last event of type `injury`, `lost_time_injury` or `fatal`, commuting accidents included | Near misses and incidents are not injuries; the counter is conservative |
| Hours month | month of `check_in` in UTC | Attendance stores UTC; the shift across midnight on the last day of a month is negligible for a yearly rate |
| Officer access to HR | read on `hr.employee` and `hr.department` for Safety officers | Needed to pick the injured employee without granting HR rights |
| Actions as activities | `mail.activity` on the event, responsible = assigned user | Reuses the standard activity queue |
| Close guard | refused while any action is `open` | Corrective actions must be closed before the event |
| Non-employee injured person | optional `partner_id`, otherwise free text | Contractors and visitors are often not employees |
| Export | list view export to XLSX (standard Odoo) | Client chose list + XLSX for v1 (D3) |

## Decisions from the client

| Nr. | Decision | Answer |
|---|---|---|
| D1 | Source of hours worked for LTIFR | `hr_attendance`, sum of `worked_hours` per company and month |
| D2 | Accidents on the way to or from work | Recorded with an `is_commute` flag, excluded from LTIFR, shown separately |
| D3 | Output form of the register in v1 | List view with XLSX export; no official printable layout |

## Out of scope

- Official register layout and printable report (D3: deferred).
- Electronic transmission to ITM or any authority; deadlines for notifying authorities.
- Medical files, sick-leave records, days lost (only the event itself, no days count in v1).
- Risk assessment (`risk matrix`), training records, PPE inventory, safety inspections.
- Equipment link to `maintenance` and product link to `quality`.
- Consolidation across companies.
- Hours of contractors (not in attendance).
- OEE, MTBF/MTTR (already native in Odoo).
