# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, models


class CommissionUpdatePurchasePrice(models.TransientModel):
    _inherit = "commission.update.purchase.price"

    @api.model
    def _default_line_domain(self):
        # without a selection: the paid lines whose commission is not computed yet
        return super()._default_line_domain() + [("commission", "=", 0.0)]
