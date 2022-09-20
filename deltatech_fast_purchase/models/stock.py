# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # l10n_ro_notice = fields.Boolean()

    def action_view_invoice(self):
        if self.purchase_id:
            return self.purchase_id.with_context(create_bill=True, notice=self.l10n_ro_notice).action_view_invoice()
