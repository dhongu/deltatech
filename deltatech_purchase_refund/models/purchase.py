# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.tools.float_utils import float_compare


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_view_invoice(self):
        action = super(PurchaseOrder, self).action_view_invoice()
        invoice_type = "in_invoice"
        for line in self.order_line:
            if line.product_id.purchase_method == "purchase":
                qty = line.product_qty - line.qty_invoiced
            else:
                qty = line.qty_received - line.qty_invoiced
            if qty < 0:
                invoice_type = "in_refund"
        action["context"]["default_type"] = invoice_type
        action["context"]["default_invoice_date"] = self.date_planned

        notice = self.env.context.get("notice", False)
        if not notice:
            for picking in self.picking_ids:
                notice = notice or picking.notice

        action["context"]["notice"] = notice
        return action


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if move.type == "in_refund":
            if self.product_id.purchase_method == "purchase":
                qty = self.qty_invoiced - self.product_qty
            else:
                qty = self.qty_invoiced - self.qty_received
            if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
                qty = 0.0
            res["quantity"] = qty
        return res
