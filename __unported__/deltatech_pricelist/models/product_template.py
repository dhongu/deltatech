# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id


    price_currency_id = fields.Many2one('res.currency', string='Price List Currency', default=_default_currency)

    @api.multi
    def price_compute(self, price_type, uom=False, currency=False, company=False):

        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])

        templates = self.with_context(currency=False)
        prices = super(ProductTemplate, templates).price_compute(price_type, uom, currency=False,  company=company)
        if price_type in ['list_price', 'list_price']:  # pretul pubilc poate fi in euro !
            for template in self:

                prices[template.id] = template.price_currency_id.compute(prices[template.id],
                                                                         currency or template.currency_id, round=False)


        return prices
