Module Line Counter
===================

This module adds a wizard to count lines of code in selected Odoo modules.
It provides a quick way to estimate the size and complexity of modules by counting lines in `.py`, `.xml`, `.js`, `.css`, and `.scss` files.
Tests are excluded from the count.
The result is an estimate: only non-empty lines are counted (comments and docstrings included), only the file types above are considered, and files that cannot be read as UTF-8 are skipped.
