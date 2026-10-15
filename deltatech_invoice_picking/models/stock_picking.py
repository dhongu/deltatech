# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from ast import literal_eval

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockPicking(models.Model):
    _inherit = "stock.picking"

    account_move_id = fields.Many2one("account.move")
    to_invoice = fields.Boolean("To invoice")
    supplier_invoice_number = fields.Char("Supplier Invoice No")

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            if picking.sale_id or picking.purchase_id:
                picking.write({"to_invoice": True})
        return res

    def action_create_invoice(self):
        for picking in self:
            if picking.state != "done":
                raise UserError(self.env._("You cannot invoice unconfirmed pickings (%s)") % picking.name)
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
                raise UserError(self.env._("You cannot invoice unconfirmed pickings (%s)") % picking.name)
            if not picking.supplier_invoice_number:
                raise UserError(self.env._("Please enter supplier invoice number"))
        self._check_receipts_billable()
        for picking in self:
            picking.purchase_id.write({"partner_ref": picking.supplier_invoice_number})
        return self.purchase_id.with_context(receipt_picking_ids=self.ids).action_create_invoice()

    def _check_receipts_billable(self):
        """Refuse a supplier bill when the selected receipts have nothing left to bill."""
        precision = self.env["decimal.precision"].precision_get("Product Unit")
        purchase_lines = self.move_ids.filtered(lambda m: m.state == "done").purchase_line_id
        if not purchase_lines or all(
            float_is_zero(line.qty_to_invoice, precision_digits=precision) for line in purchase_lines
        ):
            raise UserError(self.env._("The selected receipts are already billed: %s", ", ".join(self.mapped("name"))))
