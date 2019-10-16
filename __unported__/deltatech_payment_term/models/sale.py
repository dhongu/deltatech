# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details



 
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning



class sale_order(models.Model):
    _inherit = 'sale.order'
    
    sale_in_rates = fields.Boolean(string="Sale in Rates", compute="_compute_sale_in_rates",store=True)


    @api.multi
    @api.depends('payment_term_id')
    def _compute_sale_in_rates(self):
        for sale in self:
            sale_in_rates = False
            if sale.payment_term_id:
                if len(sale.payment_term_id.line_ids) > 1:
                    sale_in_rates = True
             
                
            sale.sale_in_rates = sale_in_rates
            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
