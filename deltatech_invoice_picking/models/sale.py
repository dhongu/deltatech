# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        invoice_line = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if "pinking_ids" in self.env.context:
            pinkings = self.env["stock.picking"].browse(self.env.context["pinking_ids"])
            for move_line in pinkings.move_lines:
                if "product_id" in invoice_line and invoice_line["product_id"] == move_line.product_id.id:
                    invoice_line.update({"quantity": move_line.quantity_done})
        return invoice_line
# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     def _create_invoices(self, grouped=False, final=False, date=None):
#         moves = super(SaleOrder, self)._create_invoices(grouped, final, date)
#
#         if "pinking_ids" in self.env.context:
#             products_qty = {}
#             pinkings = self.env["stock.picking"].browse(self.env.context["pinking_ids"])
#             for move_line in pinkings.move_lines:
#                 if move_line.product_id.id in products_qty:
#                     products_qty[move_line.product_id.id] += move_line.quantity_done
#                 else:
#                     products_qty[move_line.product_id.id] = move_line.quantity_done
#
#             for move in moves:
#                 for line in move.line_ids:
#                     if line.product_id.type == "product" and line.product_id.id not in products_qty:
#                         line.with_context(check_move_validity=False).unlink()
#                     else:
#                         products_qty[line.product_id.id] -= line.quantity
#                 move.with_context(check_move_validity=False)._recompute_dynamic_lines()
#             # todo: de verificat catitatile ramase
#         return moves
