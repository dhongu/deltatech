# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _get_default_sending_methods(self, move) -> set:
        """A partner with "Green Invoice" does not get the PDF downloaded by default.

        Odoo 19 downloads the invoice when the `manual` sending method is selected;
        for these partners it is replaced by e-mail. Picking it in the wizard still
        works: only the default changes.
        """
        methods = super()._get_default_sending_methods(move)
        if "manual" in methods and move.commercial_partner_id.print_green_invoice:
            methods = (methods - {"manual"}) or {"email"}
        return methods
