# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class UomUom(models.Model):
    _inherit = "uom.uom"

    def _dt_root_uom(self):
        """Root of the unit hierarchy, walking up `relative_uom_id`.

        Odoo 19 removed the unit category (`category_id` / `uom_type` are gone)
        and `_compute_price` / `_compute_quantity` convert ANY pair of units
        using their absolute factors. Since the root of the kilogram hierarchy
        is the gram, converting kg to Units "succeeds" and returns a value that
        is off by a factor of 1000. Comparing roots is the only way left to tell
        whether two units belong to the same family.

        Empty recordset in, empty recordset out, so it can be called defensively
        without `ensure_one`.
        """
        uom = self[:1]
        seen = set()
        while uom.relative_uom_id and uom.id not in seen:
            seen.add(uom.id)
            uom = uom.relative_uom_id
        return uom
