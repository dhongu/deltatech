# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, tools, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class account_config_settings(models.TransientModel):
    _inherit = 'account.config.settings'
    
    
    @api.multi
    def set_default_taxes(self):
        super(account_config_settings,self).set_default_taxes()
        config = self
        #config.default_sale_tax
        #config.default_purchase_tax
        print "setez noile cote de TVA"
        products = self.env['product.template'].search([])
        print "Nr prod", len(products)
        products.write({
                        'taxes_id':[(6,0,[config.default_sale_tax.id])],
                        'supplier_taxes_id':[(6,0,[config.default_purchase_tax.id])]
                        })
        products.recompute()
        # de recalculat totalul din comenzile de vanzare
        # comenzi de vanzare deschise
        order_lines = self.env['sale.order.line'].search([('invoiced','=',False),('state','not in',['done','cancel'])])
        print " Linii de comenzi de vanzare", len(order_lines)
        order_lines.write({'tax_id':[(6,0,[config.default_sale_tax.id])]})
        
        
        # de recalculat totalul din comenzile de achizitie
        # comenzi de achizitie deschise
        order_lines = self.env['purchase.order.line'].search([('invoiced','=',False),('state','not in',['done','cancel'])])
        print " Linii de comenzi de achizitie", len(order_lines)
        order_lines.write({'taxes_id':[(6,0,[config.default_purchase_tax.id])]})
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        