Declare the field as `Text` on your model:

```python
notes = fields.Text(string="Notes")
```

Then use the `markdown` widget in the form view:

```xml
<field name="notes" widget="markdown"/>
```

Supported options:

- `min_height` — minimum height of the editing area, in pixels (default `160`):

```xml
<field name="notes" widget="markdown" options="{'min_height': 300}"/>
```

The widget honors `readonly`: in read-only mode it renders the Markdown as HTML,
without the toolbar.
