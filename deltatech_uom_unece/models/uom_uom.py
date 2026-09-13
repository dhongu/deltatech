# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    unece_code_id = fields.Many2one(
        "uom.unece.code",
        string="UNECE Code",
        help="Code sent in electronic documents (e-invoice, eTransport) for this unit. "
        "When empty, the code built into Odoo is used.",
    )

    def _get_unece_code(self):
        """Return the code set on the unit, falling back to the built-in mapping.

        Core maps a unit to its code exclusively through the XML ID, against a
        fixed dictionary of 28 entries (`account/models/uom_uom.py`), and returns
        `'C62'` — one piece — for anything it does not recognise, without raising.
        Two consequences, both silent:

        * every unit a customer creates is declared as a piece, no matter what it
          measures. There is no data fix for this: a unit like "Box of 13 kg" has
          no entry in the dictionary to point at.
        * some units shipped by Odoo itself are declared as pieces too, because
          the dictionary lists XML IDs that no longer match the ones in the data:
          it expects `uom.uom_square_meter` and `uom.uom_square_foot`, while
          `uom/data/uom_data.xml` defines `uom.product_uom_square_meter` and
          `uom.product_uom_square_foot`. The millilitre is missing outright.
          Square metres, square feet and millilitres therefore all travel as
          `C62`.

        An explicit code wins over the built-in mapping rather than only filling
        in for it, because correcting a wrong built-in mapping is half the point
        of the field. Leaving the field empty changes nothing, which is what
        makes this module safe to install on a running database.

        No `ensure_one()`: core copes with an empty recordset — an invoice line
        without a product reaches this through an empty `uom_id` and gets `C62` —
        and `self.unece_code_id.code` is falsy there, so the fallback still runs.
        """
        return self.unece_code_id.code or super()._get_unece_code()
