Business code often needs to know which attribute of a variant is *the* variety, *the*
size or *the* quality grade — to fill a lot, print a delivery note or group a report.
Finding that attribute by its name is fragile: the name is translatable, consultants
rename attributes, and one client calls it `Variety` while another calls it `Soi`.

This module adds a **Role** to product attributes. Modules that need an attribute ask
for it by role, and the attribute keeps working whatever it is called.

Key business benefits:

- **Rename and translate freely.** Changing the name of an attribute, or the language
  it was entered in, no longer breaks lots, reports or printed documents that rely on it.
- **One attribute per role.** The database refuses a second attribute with the same
  role, so there is never a doubt which one a document reads.
- **Shared by several modules.** Each module adds the roles it needs; the field, the
  rule and the lookups are the same for all of them.

The module defines no roles of its own. It is a technical base for the modules that add
them (for example the apple grading modules, with variety, quality and size).
