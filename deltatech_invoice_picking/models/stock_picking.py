# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from ast import literal_eval

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_create_invoice(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
        context = literal_eval(action.get("context", "{}"))
        context.update(
            {
                "active_id": self.sale_id.id if len(self) == 1 else False,
                "active_ids": self.mapped("sale_id").ids,
                "active_model": "sale.order",
                "default_company_id": self.company_id.id,
                "pinking_ids": self.ids,
            }
        )
        action["context"] = context
        return action
