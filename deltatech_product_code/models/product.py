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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, RedirectWarning


class product_category(models.Model):
    _inherit = 'product.category'

    sequence_id = fields.Many2one('ir.sequence', string='Code Sequence')


class product_template(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(required=True)

    _sql_constraints = [
        ('name_code', 'unique (default_code,active,company_id)', "Internal Reference already exists !"),
    ]


    @api.multi
    def button_new_code(self):
        for product in self:
            if product.default_code in [False, '/', 'auto'] or self.env.context.get('force_code', False):
                if product.categ_id.sequence_id:
                    default_code = self.env['ir.sequence'].next_by_id(product.categ_id.sequence_id.id)
                    vals = {'default_code': default_code}
                    if product.default_code:
                        vals['alternative_ids'] = [(0, False, {'name': product.default_code})]
                    product.write(vals)

        action = self.env.ref('deltatech_product_code.action_force_new_code')
        action.unlink_action()

    @api.multi
    def force_new_code(self):
        self.with_context(force_code=True).button_new_code()

    @api.model
    def show_not_unique(self):
        sql = '''
            SELECT id FROM
              (SELECT pt.id, default_code, count(*) 
                   OVER   (PARTITION BY  default_code, pt.active) AS count
                    FROM product_template as pt join product_product as pp on pp.product_tmpl_id = pt.id) 
               tableWithCount
              WHERE tableWithCount.count > 1;
        '''
        self.env.cr.execute(sql)
        product_ids = [x[0] for x in self.env.cr.fetchall()]

        action = self.env.ref('deltatech_product_code.action_force_new_code')
        action.create_action()

        action = self.env.ref('product.product_template_action').read()[0]

        action['domain'] = [('id', 'in', product_ids)]
        return action


class product_product(models.Model):
    _inherit = 'product.product'

    @api.multi
    def button_new_code(self):
        for product in self:
            if product.default_code in [False, '/', 'auto'] or self.env.context.get('force_code', False):
                if product.categ_id.sequence_id:
                    default_code = self.env['ir.sequence'].next_by_id(product.categ_id.sequence_id.id)
                    if product.default_code:
                        vals['alternative_ids'] = [(0, False, {'name': product.default_code})]
                    vals = {'default_code': default_code}
                    product.write(vals)
