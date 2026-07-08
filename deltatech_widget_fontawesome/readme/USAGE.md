This is a developer-facing form widget, not a standalone feature — it adds a `fontawesome` widget usable on `char`, `text` or `selection` fields in any view.

1. In a form/list view, add the widget to the field that stores the icon class name, e.g.:
   `<field name="icon" widget="fontawesome" />`
2. The field displays the corresponding Font Awesome icon instead of the raw class name (for example a field containing `fa-star` renders the star icon), with the capitalized class name as tooltip.
3. Optionally pass an `icons` option (a mapping of allowed icons) via `options="{...}"` to restrict/label the choices offered.
