from odoo import fields, models, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def action_cancel(self):
        ExistingProcurement = self.env['stock.scheduler.existing.procurement']
        ProcurementGroup = self.env['procurement.group']
        for order in self:
            procurement_group = self.env['procurement.group'].search([('name', '=', order.origin)])
            existing_procurement = ExistingProcurement.search([('procurement_group_id', '=', procurement_group.id), ('product_id', '=', order.product_id.id)])
            existing_procurement._decrease_qty_or_unlink(order.product_qty)

        super(MrpProduction, self).action_cancel()
