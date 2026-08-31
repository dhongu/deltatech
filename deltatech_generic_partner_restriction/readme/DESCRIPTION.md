This module has been merged into **Deltatech Generic Partner**
(`deltatech_partner_generic`) and is now empty: it only keeps the dependency,
so databases that have it installed pick the restrictions up on upgrade without
any manual step.

The functionality it used to provide — restricted payment journals and the
refusal to validate a customer invoice issued to the generic partner — is
unchanged, it simply lives in `deltatech_partner_generic` now. The journals
ticked as restricted are preserved by the migration script of that module.

New installations should install `deltatech_partner_generic` directly.
