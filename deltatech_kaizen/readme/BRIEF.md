# Brief: deltatech_kaizen

Language: English for the suite documentation, as in the `readme/` fragments. Discussion with the
user stays in Romanian.

## Request

"Modul nou pentru îmbunătățire focalizată (Kaizen) pentru Odoo 20: proiecte de îmbunătățire legate
de o pierdere măsurată, analiza cauzei rădăcină (5 Why și diagrama Ishikawa), acțiuni cu responsabil
și termen, urmărirea economiilor realizate față de linia de bază." (Terrabit, 2026-11-17)

## Scope

A plant or office team sees a measurable loss (scrap, rework, downtime, overtime, material waste) and
wants to fix it in a controlled way. Odoo has no native place to record the baseline, the root cause
analysis, the owners of corrective actions and the money saved afterwards. Quality Alerts covers a
single incident with one root cause field; it does not keep a baseline or savings. `deltatech_kaizen`
gives one project per improvement: baseline, 5 Why, Ishikawa, actions with owner and deadline, and the
monthly loss measured after the fix.

## Who operates

- Kaizen user (`deltatech_kaizen.group_kaizen_user`, implies `base.group_user`): creates projects,
  writes analysis and actions, closes actions.
- Kaizen manager (`deltatech_kaizen.group_kaizen_manager`, implies the user group): may also delete
  projects and move a project to done or cancelled.

## Framing

- Suite and technical name: `deltatech` / `deltatech_kaizen`. Generic functional module, not
  Terrabit-branded: the `terrabit` suite holds branded and infrastructure modules, deltatech holds
  the functional modules for customers.
- New module, not an extension of any module.
- `depends`: `["mail"]` only. `mail` gives chatter and activities on the project. Justification for
  what is left out: no `quality` (Enterprise only, would make the module unusable on Community
  databases and it is not needed for v1); no `project` (action owner and deadline are fields here,
  a task per action adds nothing the brief asks for).
- New models: `kaizen.project`, `kaizen.why`, `kaizen.ishikawa.cause`, `kaizen.action`.
- Standard models extended: none.

## Flow

1. Create a project: name, loss type, responsible, start date, deadline, currency, baseline loss
   per month (amount) and optional target per month. State: Draft.
2. Record the baseline: `baseline_date` and `baseline_value` (loss per month, measured before the
   fix).
3. Press "Start analysis". State: Analysis.
4. Fill in the 5 Why chain (up to 5 lines), mark exactly one line as root cause.
5. Fill in Ishikawa causes grouped in the six categories (Man, Machine, Method, Material,
   Measurement, Environment).
6. Press "Start actions". State: Actions. Create actions with name, responsible and deadline.
7. Mark actions done as they finish; the done date is set automatically.
8. Press "Start verification" once every action is done. State: Verification. Record
   `measured_date` and `current_value` (loss per month measured after the fix).
9. Press "Close project" when the savings are checked. State: Done.
   Done is allowed only when: a root cause exists, no action is open and baseline is positive.

"Cancel" is available from any state except Done and moves the project to Cancelled.

## Acceptance criteria

- **CA1:** New project in Draft: `reference` is filled automatically from the sequence `KZN/00001`
  style, and the project cannot be saved without a name.
- **CA2:** `baseline_value` or `current_value` below zero: save fails with a ValidationError.
- **CA3:** `savings_monthly` = `baseline_value` − `current_value`. If `current_value` is larger than
  the baseline, the savings are negative and the project is still saved.
- **CA4:** `savings_annual` = `savings_monthly` × 12, labelled as a projection in the form.
- **CA5:** `is_target_reached` is True when `target_value` > 0 and `current_value` ≤ `target_value`,
  False otherwise.
- **CA6:** A sixth `kaizen.why` line on the same project: save fails with a ValidationError.
- **CA7:** Two `kaizen.why` lines flagged as root cause on the same project: save fails with a
  ValidationError.
- **CA8:** `date_deadline` earlier than `date_start`: save fails with a ValidationError.
- **CA9:** An action without responsible or without deadline cannot be saved (required fields).
- **CA10:** An action whose deadline is before today and that is not done shows `is_overdue` True;
  once done, `is_overdue` is False and `done_date` is today.
- **CA11:** "Close project" with an open action raises a UserError naming the open actions count.
- **CA12:** "Close project" with no root cause raises a UserError.
- **CA13:** "Close project" on a valid project (root cause set, all actions done, baseline > 0) moves
  the state to Done and sets `date_closed`.
- **CA14:** "Cancel" moves the project to Cancelled from Draft, Analysis, Actions and Verification;
  from Done the button is not offered.
- **CA15:** A user with only `group_kaizen_user` cannot unlink a project (access denied); a manager
  can.
- **CA16:** Each Ishikawa cause shows its category in the project form and in the list; the
  "Ishikawa" menu opens all causes grouped by category (six groups, one per category).

## Edge cases

- An action set to done again keeps its original `done_date` (only the first transition sets it).
- Deleting a project deletes its why lines, Ishikawa causes and actions (`ondelete="cascade"`).
- A project with no currency uses the company currency.
- Multi-company: the project belongs to the company of the user who creates it (default) and the
  record rule of the company applies; v1 does not check cross-company responsible users.
- Overdue and target flags are computed, not stored: a project not touched for a month still shows
  the correct flag on read.

## Decisions taken

| Decision | Chosen option | Reason |
|---|---|---|
| Suite | deltatech | Generic functional module; terrabit suite is for branded and infrastructure modules. |
| Technical name | `deltatech_kaizen` | Follows the `deltatech_<domain>` convention. |
| Dependencies | `mail` only | Quality is Enterprise-only; project would add tasks nothing in the brief needs. |
| Overlap with Quality Alerts | No link in v1 | Quality Alerts stays the incident record; Kaizen is the improvement project. Adding a link later needs `quality`. |
| Overlap with the Safety register | No model, no link | Safety register is built in a parallel session (`modul-safety`); Kaizen does not record incidents. A link can be added after that module lands on 20.0. |
| Loss unit | Amount per month in company currency (currency field on the project) | One unit gives comparable savings; quantity-based losses can be expressed as an amount. |
| Savings horizon | Monthly, with annualized projection ×12 | Simple, labelled as projection. |
| 5 Why | Up to 5 free-text lines, one root cause flag | Matches the method; a tree structure is more than the brief needs. |
| Ishikawa | Six fixed categories as a grouped list in the form | Standard 6M categories; a graphical diagram is out of scope for v1. |
| Access | User: CRUD, no delete; manager: full | Matches the two roles of the request. |
| Sequence | `KZN/` prefix, `ir.sequence` | Consistent references across projects. |

## Open decisions

None at implementation start. The decisions above were taken without asking; the customer can
redirect them later.

## Out of scope

- A graphical Ishikawa diagram (SVG or JS widget).
- A link to Quality Alerts (`quality.alert`) or to the Safety incident register.
- Posting savings to accounting, or an analytic account per project.
- Multi-currency conversion of the baseline and savings.
- Automatic reading of loss figures from stock, quality or manufacturing data.
- Excel export and dashboards.
- Translations other than the English source (`i18n/ro.po` is a follow-up).
- Icon and Apps Store banner (follow-up, skills `iconita-modul` and `banner-modul`).
