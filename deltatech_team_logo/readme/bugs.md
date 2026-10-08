# Known bugs

Review date: 2026-10-08. Target version: Odoo 19.

## TLOGO-001 — P3: Field help texts are written in Romanian in the source

- **Status:** Open on 19.0 and 20.0.
- **Location:** `models/crm_team.py`, line 12 (`logo`); `models/stock_picking.py`, line 14 (`team_id`).
- **Trigger:** A user whose language is not Romanian hovers over the Logo field of a sales team or the Sales Team field of a transfer.
- **Actual behavior / impact:** The tooltips ("Logo afișat în rapoartele…", "Echipa de vânzare a comenzii sursă…") are shown in Romanian to every user, while the labels and the Apps page are in English.
- **Evidence:** Source inspection.
- **Suggested fix:** Write the help texts in English (for example "Logo printed on the reports (invoice, quotation, delivery slip) issued for this sales team. If empty, the company logo is used." and "Sales team of the source order, used for the logo on the reports."), move the Romanian texts to `i18n/ro.po` and regenerate the `.pot`.
- **Validation needed:** The tooltips are English for an English user and Romanian for a Romanian user.
- **Limitations:** Translation only; no change in behavior.
