The `deltatech` module is the foundational technical dependency for the entire Deltatech suite
of Odoo addons. It provides shared base extensions and minor infrastructure improvements that
all other Deltatech modules rely on for consistent behaviour.

**✨ Key features:**

- Adds a `model_name` convenience field on access records (`ir.access`, which replaces record
  rules in Odoo 20), displaying the technical model name directly on the form alongside the
  domain widget.
- Enhances the access domain editor to use the interactive domain widget, reducing
  configuration errors when writing access restrictions and permissions.
- Removes the external link from the module form view to keep the Apps interface clean in
  private Odoo instances.
- Acts as a single installation point — installing any other Deltatech module automatically
  pulls in this base module.

This module has no user-facing menus or workflows. It is a pure technical dependency intended
for Odoo developers and system administrators maintaining the Deltatech addon suite.
