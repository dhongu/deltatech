# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def default_get(self, fields_list):
        active_model = self.env.context.get("active_model", False)
        active_ids = self.env.context.get("active_ids", [])
        self_with_context = self
        if active_model == "stock.picking":
            pickings = self.env[active_model].browse(active_ids)
            active_id = pickings.sale_id.id if len(pickings) == 1 else False
            active_ids = pickings.mapped("sale_id").ids
            self_with_context = self.with_context(
                active_id=active_id, active_ids=active_ids, active_model="sale.order", active_domain=[]
            )

        defaults = super(SaleAdvancePaymentInv, self_with_context).default_get(fields_list)

        return defaults
