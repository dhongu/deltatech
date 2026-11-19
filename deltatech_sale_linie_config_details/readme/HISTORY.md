# Changelog

## 20.0.1.1.0 (2026-11-19)

- Moved into the deltatech suite from the Maxima and Printoteca project repos; the technical name
  does not change.
- Reads details written as a JSON text or as the text of a Python list (19.0 importers), never
  evaluating them; a dictionary without `name` / `value` is shown as an unnamed group; number values
  are shown like texts.
- The **Details** button is an icon (ⓘ, text as tooltip) at the end of the line, after the
  amounts: between the description and the quantity it took width from those columns.
- The popup is a compact table, one row per group: values on one line, never broken inside;
  nested groups on compact lines. Pictures keep their proportions, with a translatable
  *Open image* link under them; `src` pictures are larger, as on 19.0.
- Upgrade from 19.0: the text column is converted to JSON before the update, instead of being
  dropped by Odoo.

## 20.0.1.0.0 (2026-11)

- Port to 20.0 in the Maxima repo: the field is `fields.Json` instead of `Text`, the `eval`
  fallback is gone, every text is escaped, the **Details** button has its own column.
