# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
 


class product_product(models.Model):
    _inherit = 'product.product'


    # price_extra - valoarea extra pret in functie de atribute
    # list_price - pretul de lista a produsului
    # lst_price - pretul de lista a produsului + pretul exta
    # price_extra_variant - valoarea extra de pret a variantei
    
    # lst_price = list_price + price_extra + price_extra_variant
    #price_extra_variant = lst_price - list_price - price_extra

    list_price = fields.Float()
    price_extra = fields.Float()
    price_extra_variant = fields.Float( string="Variant Public Price", digits=dp.get_precision('Product Price') )
    lst_price = fields.Float(comupte="_product_lst_price", inverse="_set_product_lst_price")
    # fields.function(_product_lst_price, fnct_inv=_set_product_lst_price, type='float', string='Public Price', digits_compute=dp.get_precision('Product Price')),


    @api.depends('list_price','price_extra','price_extra_variant')
    def _product_lst_price(self):
        print "Calcul lst price"       
        for product in self:
            if 'uom' in self.env.context:
                uom = product.uos_id or product.uom_id
                price = self.env['product.uom']._compute_price( uom.id, product.list_price, self.env.context['uom'])
            else:
                price = product.list_price
            self.lst_price =  price + product.price_extra + product.price_extra_variant
        
    def _set_product_lst_price(self):
        print "lst_price"
        for product in self: 
            if 'uom' in self.env.context:
                uom = product.uos_id or product.uom_id
                lst_price = self.env['product.uom']._compute_price(self.env.context['uom'] , product.list_price, uom.id)
            else:
                lst_price = product.lst_price
            self.price_extra_variant =  lst_price - product.list_price - product.price_extra   
        



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: