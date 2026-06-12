**Markdown Field Widget** adds a new OWL field widget — **`markdown`** — for any
`Text` field in the Odoo backend.

It gives users a familiar **WYSIWYG** editing experience (bold, italic,
strikethrough, headings, lists, quotes, code blocks, links), while keeping the
stored value as **raw Markdown**. The text in the database stays portable, easy to
version and perfectly readable outside of Odoo.

Conversions happen entirely in the browser, with no server-side dependency at
runtime:

- on **load**: Markdown → HTML (the [marked](https://marked.js.org/) library);
- on **save**: HTML → Markdown (the [turndown](https://github.com/mixmark-io/turndown) library).

Both libraries are bundled locally as UMD builds, so the module works offline and
needs no external CDN.

**Key features**

- WYSIWYG toolbar: bold, italic, headings, lists, quotes, code blocks and links.
- Stores raw Markdown — portable, diff-friendly and readable anywhere.
- Instant MD ↔ HTML round-trip, fully client-side.
- Honors `readonly`: in read-only mode it renders the Markdown as HTML, without the
  toolbar.
- Configurable minimum editor height via the `min_height` option.

**Usage**

```xml
<field name="notes" widget="markdown"/>
<field name="notes" widget="markdown" options="{'min_height': 300}"/>
```
