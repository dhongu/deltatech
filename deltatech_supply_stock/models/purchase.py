from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_cancel(self):
        ExistingProcurement = self.env['stock.scheduler.existing.procurement']
        ProcurementGroup = self.env['procurement.group']
        for order in self:
            # get a list with all procurement groups that are procured by this purchase order
            origin_list = order.origin.replace(',', '').split(' ')
            procurement_groups = ProcurementGroup.search([('name', 'in', origin_list)])

            # delete all the existing procurements for the products in this purchase order for all the procurement groups
            for purchase_line in order.order_line:
                if purchase_line.product_qty > 0.0:
                    for origin in origin_list:
                        existing_proc = ExistingProcurement.search([('procurement_group_id', 'in', procurement_groups.ids), ('product_id', '=', purchase_line.product_id.id)])
                        existing_proc._decrease_qty_or_unlink(purchase_line.product_qty)

        super(PurchaseOrder, self).button_cancel()
