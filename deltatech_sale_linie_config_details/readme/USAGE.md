The details are written by connectors and importers (a window configurator, a marketplace) into
the `config_details` field of the sale order lines; they cannot be typed or edited from the
interface. The module has no settings and no menu of its own.

1. Open the order created by the connector (*Sales → Orders → Quotations*, or *Sales → Orders →
   Orders* once confirmed). In the **Order Lines** tab, the lines with a configuration have a
   **Details** button, in its own column before **Quantity**; lines without details (a service,
   for instance) have no button.

   ![Quotation for Casa Verde Residence SRL, Order Lines tab: the lines Fereastră PVC 2 canate and Ușă balcon PVC have the Details button, highlighted, in its own column before Quantity; the Montaj tâmplărie line has no button](static/description/en/01_comanda_buton_detalii.png)

2. Click **Details** to open the read-only **Config Details** popup: group names in bold, values as
   `key: value` (numbers are shown like texts), nested groups on their own rows, and a group with a
   plain text value on one row as `name: value`. The `id` key is never shown. **Close** returns to
   the order.

   ![Config Details popup of the Fereastră PVC 2 canate line: the bold groups Identitate, Dimensiuni, Profil, Culoare, Părți, Schiță and Observații, highlighted; values such as Poziție P1, H 1400 and L 1200 mm, the nested parts with x, y and opening, the sketch with its Open image link, and the Close button](static/description/en/02_popup_detalii_fereastra.png)

3. Values under the keys `image` and `src` are shown as pictures (`src` larger), each with an
   **Open image** link that opens it in a new browser tab.

   ![Config Details popup of the Ușă balcon PVC line: the Machetă group with a large and a small picture of the door, highlighted, each with its Open image link](static/description/en/03_popup_detalii_imagini.png)

Format of the field: a list of `{"name": ..., "value": ...}` groups, where `value` is a text or a
dictionary whose values are texts, numbers or dictionaries. Other values (lists, booleans, empty
texts) are not shown. The order of the groups is kept; the order of the keys inside a dictionary
is not kept (the database stores them sorted, shorter keys first).

The details are copied when the order is duplicated and are not printed on the standard quotation,
delivery or invoice reports. Project reports can print them with `get_html_config_details()` and
`get_images_config_detail()` (the `image` URLs of the groups).
