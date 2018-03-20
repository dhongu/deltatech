from odoo import api, models, fields

from odoo.addons import decimal_precision as dp



class StockSchedulerExistingProcurement(models.Model):
    _name = 'stock.scheduler.existing.procurement'
    _description = 'The existing procurement orders for a specific product,proc_group and location'

    # name = fields.Char(string='Description', compute='_compute_name')
    procurement_group_id = fields.Many2one(comodel='procurement.group', string='Procuremend Group', required=True, index=True, ondelete='cascade')
    product_id = fields.Many2one(comodel="product.product", string="Product", required=True, index=True, ondelete='cascade')
    quantity = fields.Float(string='Procurement quantity', digits=dp.get_precision('Product Unit of Measure'), required=True)
    procurement_type = fields.Selection([('buy', 'Purchase Order'), ('manufacture', 'Manufacturing Order')], string='Procurement Type', required=True)
    location_id = fields.Many2one(comodel='stock.location', string='Location', required=True, ondelete='cascade')

    # @api.onchange('quantity')
    # def onchange_quantity(self):
    #     raise Warning("ONCHANGE REACHED")
    #     if self.quantity == 0.0:
    #         self.unlink()

    def _decrease_qty_or_unlink(self, qty_to_decrease):
        if self.quantity - qty_to_decrease <= 0:
            self.unlink()
        else:
            self.quantity = self.quantity - qty_to_decrease

    
