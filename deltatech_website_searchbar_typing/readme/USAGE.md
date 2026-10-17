Add the examples inside the search form, as a hidden list with the class
`o_searchbar_typing`. Each item is one example; the optional item with the class
`o_searchbar_typing_prefix` is shown in front of every example, followed by a space.
Use list items (`li`), not `span`: Odoo translates each list item as a term of its own,
while a group of inline elements is translated as one block of HTML.

In a QWeb template that calls `website.website_search_box_input`, the body of the call is
placed inside the form:

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

On a search box placed with the Website Builder, select the search input and turn on
**Typing examples** in the panel. Edit the **Prefix** (leave it empty for none) and the
**Examples**: add, remove or drag them to change the order. The option writes the same hidden
list in the form.

The speed can be changed with data attributes on the `o_searchbar_typing` element, in
milliseconds: `data-start-delay` (1500, before the first letter), `data-type-delay` (70, per
typed letter), `data-hold-delay` (1800, how long a full example stays), `data-erase-delay`
(30, per erased letter) and `data-next-delay` (400, before the next example).

Choose examples that return results: a visitor who copies one should find something.
