Odoo stores icons as plain names (for example `fa-truck`), and a form view shows
them as raw text. This module adds a field widget that displays the icon itself
instead of its name.

**Icon preview**: a `char`, `text` or `selection` field that holds an icon name is
rendered as the icon, with a readable label of the name as tooltip (for example
*Truck* for `fa-truck`).

**Font Awesome names kept working**: Odoo 20 no longer ships Font Awesome and draws
its icons with Material Symbols. Stored Font Awesome names (`fa-globe`,
`fa fa-globe` or `globe`) are translated to the equivalent Material Symbols icon
with the official Odoo mapping. A Material Symbols name (for example `public` or
`shopping_cart`) can also be stored directly.

**One attribute to use it**: add the widget to any field in a form or list view:

```xml
<field name="icon" widget="fontawesome"/>
```

The module adds no menu and no settings. It is a technical building block for other
modules and for view customisations.

## Limitations

- The widget only displays the icon. It has no picker and no input box, so the value
  is set by code, by import or with another widget in a different view.
- A Font Awesome name without an equivalent in the mapping is shown only if it is
  also a valid Material Symbols name; otherwise nothing is displayed. An empty
  field shows nothing.
