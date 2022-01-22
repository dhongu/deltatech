# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_cancel(self):
        for order in self:
            for order_line in order.order_line:
                for move in order_line.move_ids:
                    if move.created_purchase_line_id:
                        if move.created_purchase_line_id.order_id.state == "draft":
                            move.created_purchase_line_id.unlink()

        return super(SaleOrder, self)._action_cancel()

    def _log_decrease_ordered_quantity(self, filtered_documents, cancel=True):
        documents_remove = []
        for (parent, responsible), rendering_context in filtered_documents.items():
            if parent._name == "purchase.order":
                order_exceptions, visited_moves = rendering_context
                for order_line, diff in order_exceptions.values():
                    for move in order_line.move_ids:
                        purchase_line = move.created_purchase_line_id
                        if purchase_line:
                            if purchase_line.order_id.state == "draft":
                                if purchase_line.product_qty == diff[1]:
                                    purchase_line.write({"product_qty": diff[0]})
                                    documents_remove += [(parent, responsible)]

        for item in documents_remove:
            filtered_documents.pop(item)
        return super(SaleOrder, self)._log_decrease_ordered_quantity(filtered_documents, cancel)
