The module has no menus or settings: the examples are turned on per search box, in the Website
Builder.

1. In the **Website** app, open the page with the search box and click **Edit**. Click the search
   box: the **Search** group of the **Style** tab shows the **Typing examples** switch. Turn it on,
   then edit the **Prefix** (leave it empty for none) and the **Examples**: add, remove or drag them
   to change the order. Click **Save**.

   ![Website Builder on the Search the help center page: the search box is selected; in the Search group of the right panel, the Typing examples switch is on, the prefix is e.g. and the Examples list holds e-Invoice, bank statement import and credit note](static/description/en/01_editor_exemple_tastate.png)

2. Open the page on the website, outside the editor. After about a second and a half, the
   placeholder types the first example with the prefix in front, holds it, erases it and types the
   next one.

   ![The Search the help center page on the website: the highlighted search box shows the placeholder e.g. e-Invoice, typed by the animation](static/description/en/02_exemplu_tastat.png)

3. Click in the search box or start typing: the animation stops for good on that page and the
   original placeholder comes back.

   ![The same page after a click in the highlighted search box: the placeholder is back to Search the help center... and the animation has stopped](static/description/en/03_oprire_la_click.png)

The animation runs only on the website, not in the editor. The option writes the examples in the
form as a hidden list with the class `o_searchbar_typing`; the optional item with the class
`o_searchbar_typing_prefix` is shown in front of every example, followed by a space.

**Translations.** Each example and the prefix are translation terms of their own. The list is
hidden, so the translation mode of the Website Builder does not show it: translate the examples from
the page view, in developer mode (**Settings > Technical > User Interface > Views**, the view of
the page, **Architecture** tab, translation button of the field).

In a QWeb template that calls `website.website_search_box_input`, the body of the call is
placed inside the form. Use list items (`li`), not `span`: Odoo translates each list item as a term
of its own, while a group of inline elements is translated as one block of HTML.

```xml
<t t-call="website.website_search_box_input">
    <t t-set="search_type" t-valuef="all"/>
    <t t-set="action" t-valuef="/website/search"/>
    <t t-set="placeholder">Search the user guides</t>
    <ul class="o_searchbar_typing d-none" aria-hidden="true">
        <li class="o_searchbar_typing_prefix">e.g.</li>
        <li>e-Invoice</li>
        <li>bank statement import</li>
        <li>credit note</li>
    </ul>
</t>
```

The speed can be changed with data attributes on the `o_searchbar_typing` element, in
milliseconds: `data-start-delay` (1500, before the first letter), `data-type-delay` (70, per
typed letter), `data-hold-delay` (1800, how long a full example stays), `data-erase-delay`
(30, per erased letter) and `data-next-delay` (400, before the next example).

Choose examples that return results: a visitor who copies one should find something.
