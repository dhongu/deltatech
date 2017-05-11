# -*- coding: utf-8 -*-


from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        route_buy = self.env.ref('purchase.route_warehouse0_buy')
        route_manufacture = self.env.ref('mrp.route_warehouse0_manufacture')
        for order in self:
            for line in order.order_line:
                if route_manufacture.id in line.product_id.route_ids.ids:
                    bom = self.env['mrp.bom'].serach(['|', ('product_id', '=', line.product_id.id),
                                                      ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                    if not bom:
                        raise UserError(_('Product %s without BOM') % line.product_id.name)
                else:
                    if route_buy.id in line.product_id.route_ids.ids:
                        if not line.product_id.seller_ids:
                            raise UserError(_('Product %s without vendor')  % line.product_id.name)

        return super(SaleOrderLine, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # se suprascrie metoda standard pentru a nu mai generea eroare
    def _check_routing(self):
        if self.product_id.route_ids:  # de aprovizioneaza de undeva
            is_available = True
        else:
            is_available = super(SaleOrderLine, self)._check_routing()
        return is_available
