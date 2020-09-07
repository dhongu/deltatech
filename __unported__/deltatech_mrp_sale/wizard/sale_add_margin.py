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


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class sale_add_margin(models.TransientModel):
    _name = 'sale.add.margin'
    _description = "Add margin to sale order"

    margin = fields.Float(string='Margin', required=True)

    @api.multi
    def do_add_margin(self):
        active_ids = self.env.context.get('active_ids', False)

        orders = self.env['sale.order'].browse(active_ids)

        for order in orders:
            order.button_update()  # pentru a calcula valoarea totala
            amount_before_margin = order.amount_untaxed
            for resource in order.resource_ids:
                price = resource.price_unit * (1.0 + self.margin / 100.0)
                amount = price * resource.product_uom_qty
                margin = resource.product_uom_qty * price - resource.product_uom_qty * resource.purchase_price
                resource.write({'price_unit': price,
                                'amount': amount,
                                'margin': margin})

            # recalculez valoarea din  articole
            for article in order.article_ids:
                amount = 0
                for resource in article.resource_ids:
                    amount += resource.amount
                if article.product_uom_qty:
                    price_unit = article.amount / article.product_uom_qty

                article.write({'price_unit': price_unit, 'amount': amount})

            order.button_update()  # pentru a calcula valoarea totala

            msg = _('Margin %s was added. Before added margin amount was %s, after is %s') % (
                self.margin, amount_before_margin, order.amount_untaxed)

        order.message_post(body=msg)
