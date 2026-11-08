Function:

- Block opening an item from the list when selecting text
- Deleting an unsaved one2many line twice (e.g. Enter pressed twice on its trash icon) no
  longer breaks the save of the form with a `virtual_N` id error

Functions:

- Blocheaza deschiderea unui item din lista la selecta unui text
- Stergerea de doua ori a unei linii one2many nesalvate nu mai blocheaza salvarea formularului
  cu eroarea `virtual_N`

Odoo Online
===========

The module contains no Python code at runtime, only JavaScript and a style sheet (the `tests/`
folder runs the JavaScript test in CI and is not part of the import). Besides Odoo.sh and
on-premise installations, it can be used on Odoo Online (Custom plan): download the zip and load
it from **Apps > Import Module**.
