The details are written by connectors and importers (a window configurator, a marketplace) into
the `config_details` field of the sale order lines; they cannot be typed or edited from the
interface. The module has no settings and no menu of its own.

1. Open the order created by the connector (*Sales → Orders → Quotations*, or *Sales → Orders →
   Orders* once confirmed). In the **Order Lines** tab, the lines with a configuration have a
   **Details** icon (ⓘ, the text shows on hover), in a narrow column at the end of the row, after the amount;
   lines without details (a service, for instance) have no icon.

   ![Quotation for Casa Verde Residence SRL, Order Lines tab: the lines Fereastră PVC 2 canate and Ușă balcon PVC have the Details icon (ⓘ), highlighted, in a narrow column at the end of the row, after the amount; the Montaj tâmplărie line has no icon](static/description/en/01_comanda_buton_detalii.png)

2. Click the **Details** icon to open the read-only **Config Details** popup, a compact table with one row
   per group: the group name on the left, the values on the right as `key: value`, one after the
   other and never broken inside (numbers are shown like texts); each nested group gets a compact
   line of its own, and a group with a plain text value shows the text on the right. The `id` key is never shown. **Close** returns to
   the order.

   ![Config Details popup of the Fereastră PVC 2 canate line: one table row per group, Identitate, Dimensiuni, Profil, Culoare, Părți, Schiță and Observații, highlighted; values such as Poziție P1, H 1400 and L 1200 mm, the nested parts with x, y and opening, the sketch with its Open image link, and the Close button](static/description/en/02_popup_detalii_fereastra.png)

3. Values under the keys `image` and `src` are shown as pictures that keep their proportions (`src`
   larger), each with an **Open image** link that opens it in a new browser tab.

   ![Config Details popup of the Ușă balcon PVC line: the Machetă group with a large and a small picture of the door, highlighted, each with its Open image link](static/description/en/03_popup_detalii_imagini.png)

Format of the field: a list of `{"name": ..., "value": ...}` groups, where `value` is a text or a
dictionary whose values are texts, numbers or dictionaries. Other values (lists, booleans, empty
texts) are not shown. The order of the groups is kept; the order of the keys inside a dictionary
is not kept (the database stores them sorted, shorter keys first).

The details are copied when the order is duplicated and are not printed on the standard quotation,
delivery or invoice reports. Project reports can print them with `get_html_config_details()` and
`get_images_config_detail()` (the `image` URLs of the groups).
