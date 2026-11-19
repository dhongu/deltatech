Stores the configuration of the product sold on a sale order line — dimensions, profile, colour,
parts, mock-up images — as structured data, and shows it to the salesperson from a **Details**
icon on the line.

Connectors and marketplace importers write the configuration they receive (a window configurator,
a print shop's mock-ups) into one common field, `config_details`, instead of each inventing its
own field and popup. The salesperson reads it in a popup without leaving the order.

Main features:

- `config_details` on sale order lines, a JSON field copied with the line when the order is
  duplicated.
- **Details** icon (ⓘ) in its own narrow column of the order lines, shown only on lines with details.
- Popup with the groups of details: names in bold, values as `key: value`, nested groups,
  pictures with an *Open image* link.
- Safe: every text is escaped and nothing is ever evaluated as code.
- Reads the formats written by older importers (a JSON text, or the text of a Python list) and
  converts the details of a database coming from 19.0 when it is upgraded.
- Helpers for project reports: `get_html_config_details()` and `get_images_config_detail()`.

Format of the field: a list of `{"name": ..., "value": ...}` groups, where `value` is a text or a
dictionary of texts, numbers or dictionaries. The key `id` is never shown; the keys `image` and
`src` are shown as pictures.
