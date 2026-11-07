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

**Editing.** In edit mode the toolbar sits above the field; select text and press a
button to format it. The value is saved as Markdown when you leave the field and save
the record.

![Form in edit mode: the Markdown toolbar (bold, italic, strikethrough, H1-H3, paragraph, lists, quote, code, link, clear formatting) above a text with a heading, a bulleted list, a link and a quote](static/description/en/01_editare_markdown.png)

**Read-only.** The text is shown formatted, without the toolbar.

![Read-only Markdown field showing a heading, a numbered list with bold items, a paragraph and inline code, with no toolbar](static/description/en/02_afisare_doar_citire.png)

**Safe display.** Since 19.0.1.0.5 the HTML produced from the Markdown is sanitized
before it is displayed, in edit and read-only mode, including for values stored
earlier. Harmless inline HTML such as `<kbd>` or `<mark>` keeps its formatting;
scripts, inline event handlers, `javascript:` links and embedded content (`<iframe>`,
`<object>`, `<embed>`) are not displayed. Replace embedded videos or maps with a
regular link.

Strikethrough, inline HTML such as `<kbd>` or `<mark>` and tables are not kept when
the text is edited and saved: only standard Markdown is stored.

![Read-only Markdown field where the Ctrl and S keys are boxed and a word is highlighted, while the embedded frame placed between the two paragraphs is not displayed](static/description/en/03_html_filtrat.png)
