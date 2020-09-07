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

from odoo.tools import float_compare, float_is_zero
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def button_update(self):
        for order in self:
            # exista pozitii cu unitatea de masura %
            for line in order.order_line:
                if line.product_uom.name == '%':
                    line.calc_price_percent()

    """
    @api.multi
    def _amount_all(self, field_name, arg):
        res = super(sale_order, self)._amount_all(field_name, arg)
        return res
    """


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def calc_price_percent(self):
        self.ensure_one()
        domain = eval(self.product_id.percent_domain)
        domain.extend([('order_id', '=', self.order_id.id), ('id', '!=', self.id)])

        lines = self.env['sale.order.line'].search(domain)
        total_amount = 0
        for line in lines:
            total_amount += line.price_subtotal

        total_amount = total_amount / 100

        if not float_is_zero(self.price_unit - total_amount, precision_digits=2):
            self.write({'price_unit': total_amount})


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
