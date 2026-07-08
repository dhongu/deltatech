This module is mostly a technical building block: it adds a new report type (`qweb-prn`) that other modules can use to define label/report actions containing raw ZPL text (Zebra printer syntax) instead of PDF.

For the end user, the effect shows up only when another module ships a report configured with this type (e.g. a shipping label report):

1. Print that report as usual (from the document's **Print** menu).
2. Instead of a PDF preview, the browser downloads a `.prn` file with the ZPL content.
3. On each workstation, the `.prn` file extension must be associated beforehand with a script/printer driver that forwards the file to a Zebra label printer — this is a one-time IT setup per machine, not something configured inside Odoo.

If no such report exists yet in the database, installing this module alone has no visible effect in the interface.
