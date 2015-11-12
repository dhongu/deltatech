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
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from openerp.osv.fields import related

from openerp.addons.product import _common

_logger = logging.getLogger(__name__)


ITEM_CATEG = [('primary','Primary'),('normal','Normal'),('optional','Optional'),('service','Service'),('opt_serv','Optional Service')]



class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    article_list = fields.Boolean(string='Article List')
    
    @api.model
    def _bom_explode_variants_categ(
            self, bom, product, factor, properties=None, level=0,
            routing_id=False, previous_products=None, master_bom=None, production_attr_values=None):


        routing_id = bom.routing_id.id or routing_id
        uom_obj = self.env["product.uom"]
        routing_obj = self.env['mrp.routing']
        master_bom = master_bom or bom

        def _factor(factor, product_efficiency, product_rounding):
            factor = factor / (product_efficiency or 1.0)
            factor = _common.ceiling(factor, product_rounding)
            #if factor < product_rounding:
            #    factor = product_rounding
            return factor

        factor = _factor(factor, bom.product_efficiency, bom.product_rounding)

        result = []


        for bom_line_id in bom.bom_line_ids:
            if bom_line_id.date_start and \
                    (bom_line_id.date_start > fields.Date.context_today(self))\
                    or bom_line_id.date_stop and \
                    (bom_line_id.date_stop < fields.Date.context_today(self)):
                continue
            # all bom_line_id variant values must be in the product
            if bom_line_id.attribute_value_ids:
                if not product and production_attr_values:
                    if not self._check_product_suitable(
                            production_attr_values,
                            bom_line_id.attribute_value_ids):
                        continue
                elif not product or not self._check_product_suitable(
                        product.attribute_value_ids.ids,
                        bom_line_id.attribute_value_ids):
                    continue
            if previous_products and (bom_line_id.product_id.product_tmpl_id.id
                                      in previous_products):
                raise exceptions.Warning(
                    _('Invalid Action! BoM "%s" contains a BoM line with a'
                      ' product recursion: "%s".') %
                    (master_bom.name, bom_line_id.product_id.name_get()[0][1]))

            quantity = _factor(bom_line_id.product_qty * factor,
                               bom_line_id.product_efficiency,
                               bom_line_id.product_rounding)


            if not bom_line_id.product_id:
                if not bom_line_id.type != "phantom":
                    bom_id = self._bom_find(
                        product_tmpl_id=bom_line_id.product_template.id,
                        properties=properties)
                else:
                    bom_id = False
            else:
                bom_id = self._bom_find(product_id=bom_line_id.product_id.id,
                                        properties=properties)

            if (bom_line_id.type != "phantom" and
                    (not bom_id or self.browse(bom_id).type != "phantom")):

               
                if production_attr_values:
                    product_attributes = ( bom_line_id.product_template._get_product_attributes_inherit_dict(production_attr_values))
                    comp_product = self.env['product.product']._product_find(  bom_line_id.product_template, product_attributes)
                else:
                    comp_product = bom_line_id.product_id
                    product_attributes = (  bom_line_id.product_id. _get_product_attributes_values_dict())
                    
                result.append({
                    'name': (bom_line_id.product_id.name or
                             bom_line_id.product_template.name),
                    'product_id': comp_product and comp_product.id,
                    'product_template': (
                        bom_line_id.product_template.id or
                        bom_line_id.product_id.product_tmpl_id.id),
                    'product_qty': quantity,
                    'product_uom': bom_line_id.product_uom.id,
                    'product_uos_qty': (
                        bom_line_id.product_uos and
                        _factor((bom_line_id.product_uos_qty * factor),
                                bom_line_id.product_efficiency,
                                bom_line_id.product_rounding) or False),
                    'product_uos': (bom_line_id.product_uos and
                                    bom_line_id.product_uos.id or False),
                    'product_attributes': map(lambda x: (0, 0, x),
                                              product_attributes),
                    #'level':level,
                    'item_categ':bom_line_id.item_categ,
                    #'row': bom_id is False
                })
            
            elif bom_id:
                all_prod = [bom.product_tmpl_id.id] + (previous_products or [])
                bom2 = self.browse(bom_id)
                # We need to convert to units/UoM of chosen BoM
                factor2 = uom_obj._compute_qty(
                    bom_line_id.product_uom.id, quantity, bom2.product_uom.id)
                quantity2 = factor2 / bom2.product_qty
                res = self._bom_explode_variants_categ(
                    bom2, bom_line_id.product_id, quantity2,
                    properties=properties, level=level + 1,
                    previous_products=all_prod, master_bom=master_bom, production_attr_values = production_attr_values)
                result = result + res
            else:
                if not bom_line_id.product_id:
                    name = bom_line_id.product_template.name_get()[0][1]
                else:
                    name = bom_line_id.product_id.name_get()[0][1]
                raise exceptions.Warning(
                    _('Invalid Action! BoM "%s" contains a phantom BoM line'
                      ' but the product "%s" does not have any BoM defined.') %
                    (master_bom.name, name))

        return result


class mrp_bom_line(models.Model):
    _inherit = 'mrp.bom.line'   
    item_categ = fields.Selection(ITEM_CATEG, default='normal', string='Item Category')
    
    
    _sql_constraints = [
        ('bom_qty_zero', 'CHECK (product_qty<>0)', 'All product quantities must be greater than 0.\n' \
            'You should install the mrp_byproduct module if you want to manage extra products on BoMs !'),
    ]    
    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
