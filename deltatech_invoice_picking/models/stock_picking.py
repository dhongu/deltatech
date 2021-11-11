# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from ast import literal_eval

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    account_move_id = fields.Many2one("account.move")
    to_invoice = fields.Boolean("To invoice")

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.sale_id or picking.purchase_id:
                picking.write({"to_invoice": True})
        return res

    def action_create_invoice(self):
        for picking in self:
            if picking.state != "done":
                raise UserError(_("You cannot invoice unconfirmed pickings (%s)") % picking.name)
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
        context = literal_eval(action.get("context", "{}"))
        context.update(
            {
                "active_id": self.sale_id.id if len(self) == 1 else False,
                "active_ids": self.mapped("sale_id").ids,
                "active_model": "sale.order",
                "default_company_id": self.company_id.id,
                "picking_ids": self.ids,
            }
        )
        action["context"] = context
        return action

    def action_create_supplier_invoice(self):
        for picking in self:
            if picking.state != "done":
                raise UserError(_("You cannot invoice unconfirmed pickings (%s)") % picking.name)

        return self.purchase_id.with_context(receipt_picking_ids=self.ids).action_create_invoice()
        # # action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
        # action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # context = literal_eval(action.get("context", "{}"))
        # context.update(
        #     {
        #         "active_id": self.purchase_id.id if len(self) == 1 else False,
        #         "active_ids": self.mapped("purchase_id").ids,
        #         "active_model": "purchase.order",
        #         "default_company_id": self.company_id.id,
        #         "picking_ids": self.ids,
        #     }
        # )
        # action["context"] = context
        # return action
