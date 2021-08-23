# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def default_get(self, fields_list):
        defaults = super(SaleAdvancePaymentInv, self).default_get(fields_list)
        if self._context.get("active_ids"):
            # company_id = self._context.get("company_id", self.env.user.company_id.id)
            sale_obj = self.env["sale.order"]
            order = sale_obj.browse(self._context.get("active_ids"))[0]

            partner_generic = order.company_id.generic_partner_id
            if not partner_generic:
                partner_generic = self.env.ref("deltatech_partner_generic.partner_generic")

            if partner_generic == order.partner_id:
                journal_bf_id = self.env["ir.config_parameter"].sudo().get_param("sale.journal_bf_id")
                journal_bf = self.env["account.journal"].browse(int(journal_bf_id)).exists()
                if journal_bf:
                    defaults["journal_id"] = journal_bf.id

        return defaults
