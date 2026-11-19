# Brief: deltatech_sale_linie_config_details

## Request

2026-11-19, Dorin Hongu: „vezi daca nu putem sa mutam modulul deltatech_sale_linie_config_details in
deltatech si sa-l facem ca lumea” (move the module from the Maxima project repo into the deltatech
suite and bring it to the suite standard).

The module existed in two project repos under the same technical name: `printotecaerp` (18.0/19.0,
`Text` field, used by `deltatech_marketplace_brickweb` and `terrabit_printoteca`) and `maxima`
(20.0 port, `Json` field, used by `maxima_winarhi_connector`).

## Purpose

A sale order line often sells a configured product: a PVC window with its dimensions, profile and
parts, a printed item with its mock-ups. Connectors and marketplaces receive this configuration as
structured data, but the standard line only has a text description. The module stores the
configuration on the line as JSON and lets the salesperson read it from the order, so that every
connector does not invent its own field and its own popup.

## Who operates

- Connectors and importers (code) write the details; nobody types them by hand.
- The salesperson (`sales_team.group_sale_salesman`) reads them from the order form.

## Scope

- Suite and technical name: `deltatech` / `deltatech_sale_linie_config_details` (name kept: the
  module is installed on Maxima staging and at Printoteca on 19.0).
- New module in the suite (moved from the project repos).
- `depends`: `sale` (the field is on `sale.order.line`, the button on the quotation form).
- New models: `sale.order.line.config.details` (transient, the read-only popup).
- Extended models: `sale.order.line` + `config_details` (`fields.Json`, copied with the line).

## Format

A list of `{"name": ..., "value": ...}` groups. `value` is a text or a dictionary; dictionary
values are texts, numbers or dictionaries (nesting allowed). Inside a dictionary the key `id` is
never shown, the keys `image` and `src` are shown as pictures. A dictionary without `name` and
`value`, or a group without `name`, is shown as an unnamed group. A JSON text (as written by the 19.0 importers) is read as
its content.

## Flow

1. A connector creates or updates the order with `config_details` on the lines.
2. The salesperson opens the order; lines with details have a **Details** icon (ⓘ, the text is
   the tooltip), in a narrow column at the end of the row, after the amount.
3. A click opens the *Config Details* popup: one table row per group, the name on the left,
   the values as `key: value` on one line, never broken inside, nested groups on compact lines,
   pictures (proportions kept) with an *Open image* link; *Close* returns to the order.

## Acceptance criteria

- **CA1:** a line created with a list of groups keeps it unchanged (read back equal). *(test)*
- **CA2:** in the popup, each group is one table row (name on the left); texts show as unbroken
  `key: value` pieces, nested dictionaries as compact lines, a plain text value next to its group
  name; the `id` key never shows. *(test)*
- **CA3:** text from the data is escaped (`<script>` shows as text) and never evaluated. *(test)*
- **CA4:** a line without details has no **Details** icon; malformed details (not a list of
  groups) open an empty popup, without error. *(test)*
- **CA5:** `image` / `src` values show as pictures with an *Open image* link;
  `get_images_config_detail()` returns the `image` URLs. *(test)*
- **CA6:** a salesperson clicks the **Details** icon and sees the popup with the details. *(test)*
- **CA7:** the **Details** icon (no text, tooltip *Details*) is its own narrow column at the end
  of the row, after the amounts; the description and quantity columns are as in standard Odoo. *(test)*
- **CA8:** details written as a JSON text, or as `str()` of a Python list, show like a list;
  a dictionary without `name`/`value` shows as an unnamed group; number values show. *(test)*
- **CA9:** updating a database coming from 19.0 (text column) converts the stored details to JSON
  without losing any line; a database already on 20.0 is not touched. *(test)*
- **CA10:** duplicating an order copies the details to the new lines. *(test)*

## Edge cases

- Key order: the JSON column (`jsonb`) does not keep the order of the keys inside a group; the
  popup shows them in the stored order (shorter keys first). Connectors that need an order use
  separate groups.
- Multi-company: the field follows the line; no company-specific behaviour.
- Rights: anyone who can read the order line can open the popup (the wizard is open to
  `base.group_user`; it only holds rendered HTML of a line the user already read).
- A text in the 19.0 column that is neither JSON nor a Python literal is kept as a JSON string
  (shown as nothing, but not lost).

## Decisions taken

| Decision | Choice | Reason |
|---|---|---|
| Technical name | kept `deltatech_sale_linie_config_details` | installed at two customers; a rename needs a migration on both |
| Field type | `fields.Json` | structured data, no `eval` (the 19.0 `Text` + `eval` fallback was unsafe) |
| Python-literal texts | read with `ast.literal_eval` | 19.0 importers stored `str()` of lists; literal_eval evaluates no code |
| Price | free (LGPL-3, no price) | explicit request of the user, 2026-11-19 |
| 19.0 → 20.0 data | pre-migration text → jsonb | approved, 2026-11-19; Printoteca migrates onto this module |
| Order report | not changed | approved, 2026-11-19; helpers stay available for project reports |
| Number values | shown like texts | importers send numbers (dimensions); dropping them silently hid data (presumed) |

## Out of scope

- Printing the details on the sale order, delivery or invoice reports (projects use
  `get_html_config_details()` / `get_images_config_detail()` in their own templates).
- Editing the details from the interface.
- Searching or grouping orders by a detail.
