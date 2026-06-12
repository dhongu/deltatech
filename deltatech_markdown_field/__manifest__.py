# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Markdown Field",
    "summary": "WYSIWYG markdown widget storing raw Markdown in a Text field",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Tools",
    "depends": [
        "web",
    ],
    "price": 30.00,
    "currency": "EUR",
    "license": "OPL-1",
    "data": [],
    "assets": {
        "web.assets_backend": [
            # Vendored libraries (UMD builds attach to globalThis)
            "deltatech_markdown_field/static/src/lib/marked/marked.min.js",
            "deltatech_markdown_field/static/src/lib/turndown/turndown.umd.js",
            # Widget
            "deltatech_markdown_field/static/src/fields/markdown_field.scss",
            "deltatech_markdown_field/static/src/fields/markdown_field.esm.js",
            "deltatech_markdown_field/static/src/fields/markdown_field.xml",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
