Odoo stores Font Awesome icons as plain class names (for example `fa-truck`), and a
form view shows them as raw text. This module adds a field widget that displays the
icon itself instead of its class name.

**Icon preview**: a `char`, `text` or `selection` field that holds a Font Awesome class
name is rendered as the icon, with the name of the class as tooltip.

**One attribute to use it**: add the widget to any field in a form or list view:

```xml
<field name="icon" widget="fontawesome"/>
```

The module adds no menu and no settings. It is a technical building block for other
modules and for view customisations.

## Limitations

- The widget only displays the icon. It has no picker and no input box, so the value
  is set by code, by import or with another widget in a different view.
- The field must not be empty: the tooltip is built from the stored value, and an
  empty value raises a JavaScript error in the view.
