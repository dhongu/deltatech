# -*- coding: utf-8 -*-


from odoo import api, fields, models, _



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # se suprascrie metoda standard pentru a nu mai generea eroare
    def _check_routing(self):
        if self.product_id.route_ids:  # de aprovizioneaza de undeva
            is_available = True
        else:
            is_available = super(SaleOrderLine,self)._check_routing()
        return is_available