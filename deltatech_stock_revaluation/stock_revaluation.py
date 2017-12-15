# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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
from duplicity.tempdir import default


class stock_revaluation(models.Model):
    _name = 'stock.revaluation'
    _description = "Stock Revaluation"
    _inherit = 'mail.thread'

    name = fields.Char('Reference',
                       help="Reference for the journal entry",
                       readonly=True,
                       required=True,
                       states={'draft': [('readonly', False)]},
                       copy=False,
                       default='/')
    title = fields.Char('Title',
                       help="Title for the report",
                       readonly=False,
                       required=True,
                       states={'draft': [('readonly', False)]},
                       copy=False,
                       default='PLAN AMORTIZARE ')

    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('posted', 'Posted'),
                                        ('cancel', 'Cancelled')],
                             string='Status',
                             readonly=True,
                             required=True,
                             default='draft',
                             states={'draft': [('readonly', False)]})

    # quant_ids = fields.Many2many('stock.quant', 'stock_revaluation_quant', 'valuation_id','quant_id', string='Quants')

    date = fields.Date(string="Date",
                       readonly=True,
                       required=True,
                       states={'draft': [('readonly', False)]},
                       default=fields.Date.today)
    value_type = fields.Selection([('percent', "Percent"), ('velue', 'Value')], default='percent', string="Value Type")

    type = fields.Selection([('reduction', 'Reduction'), ('growth', 'Growth')], default='reduction', string="Type",
                            readonly=True,
                            required=True,
                            states={'draft': [('readonly', False)]})
    percent = fields.Float(string='Percent',
                           readonly=True,
                           required=True,
                           states={'draft': [('readonly', False)]})

    value = fields.Float(string='Value',
                         readonly=True,
                         required=True,
                         states={'draft': [('readonly', False)]})

    line_ids = fields.One2many('stock.revaluation.line',
                               'revaluation_id',
                               string='Revaluation line quants',
                               readonly=True,
                               required=True,
                               copy=True,
                               states={'draft': [('readonly', False)]})

    company_id = fields.Many2one(comodel_name='res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})

    currency_id = fields.Many2one('res.currency', 'Currency',
                                  readonly=True,
                                  related="company_id.currency_id")

    old_amount_total = fields.Float(string="Old Amount Total", readonly=True, )
    new_amount_total = fields.Float(string="New Amount Total", readonly=True, )
    account_symbol = fields.Char(string="Cont", default='21.03')

    location_id = fields.Many2one('stock.location')


    @api.model
    def default_get(self, fields):
        defaults = super(stock_revaluation, self).default_get(fields)

        active_ids = self.env.context.get('active_ids', False)
        active_id = self.env.context.get('active_id', False)
        model = self.env.context.get('active_model', False)

        domain = False

        if model == 'stock.quant':
            domain = [('id', 'in', active_ids)]
        if model == 'stock.location':
            domain = [('location_id', '=', active_id)]
            defaults['location_id'] = active_id

        if domain:
            quants = self.env['stock.quant'].search(domain)
            defaults['line_ids'] = []
            for quant in quants:
                if not quant.init_value:
                    init_value = quant.inventory_value
                else:
                    init_value = quant.init_value
                defaults['line_ids'] += [(0, 0, {'quant_id': quant.id,
                                                 'product_id': quant.product_id.id,
                                                 'init_value': init_value,
                                                 'old_value': quant.inventory_value,
                                                 'new_value': quant.inventory_value,
                                                 })]

        return defaults

    @api.model
    def create(self, vals):
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence_revaluation = self.env.ref('deltatech_stock_revaluation.sequence_stock_revaluation')
            if sequence_revaluation:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence_revaluation.id)
        return super(stock_revaluation, self).create(vals)

    @api.multi
    def do_update(self):
        self.ensure_one()
        old_amount_total = 0.0
        new_amount_total = 0.0
        for line in self.line_ids:
            quant = line.quant_id
            if not quant.init_value:
                init_value = quant.inventory_value
            else:
                init_value = quant.init_value

            if self.value_type == 'percent':
                ajust = init_value * self.percent / 100.0
            else:
                ajust = self.value

            if self.type == 'reduction':
                ajust = -1 * ajust
            new_value = quant.inventory_value + ajust
            new_cost = new_value / quant.qty
            old_amount_total += quant.inventory_value
            new_amount_total += new_value
            values = {'init_value': init_value,
                      'old_value': quant.inventory_value,
                      'new_value': new_value}
            if init_value == quant.inventory_value:
                values['first_revaluation'] = self.date
            line.write(values)
        self.write({'old_amount_total': old_amount_total, 'new_amount_total': new_amount_total})

        if self.env.context.get('from_quants', False):
            return {
                'domain': "[('id','=', " + str(self.id) + ")]",
                'name': _('Stock Revaluation'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'stock.revaluation',
                'view_id': False,
                'type': 'ir.actions.act_window'
            }

    @api.multi
    def do_revaluation(self):
        for line in self.line_ids:
            quant = line.quant_id
            value = {}
            if not quant.init_value:
                init_value = quant.inventory_value
                value['init_value'] = init_value
                value['first_revaluation'] = self.date
            else:
                init_value = quant.init_value
            if self.value_type == 'percent':
                ajust = init_value * self.percent / 100.0
            else:
                ajust = self.value
            if self.type == 'reduction':
                ajust = -1 * ajust
            new_value = quant.inventory_value + ajust
            new_cost = new_value / quant.qty
            value['cost'] = new_cost
            quant.write(value)
        self.write({'state': 'posted'})
        if self.env.context.get('from_quants', False):
            return {
                'domain': "[('id','=', " + str(self.id) + ")]",
                'name': _('Stock Revaluation'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'stock.revaluation',
                'view_id': False,
                'type': 'ir.actions.act_window'
            }


class stock_revaluation_line(models.Model):
    _name = 'stock.revaluation.line'
    _description = 'Inventory Revaluation Line'

    revaluation_id = fields.Many2one('stock.revaluation',
                                     'Revaluation', required=True,
                                     readonly=True)

    product_id = fields.Many2one('product.product', 'Product',
                                 readonly=True,
                                 related="quant_id.product_id")

    quant_id = fields.Many2one('stock.quant', 'Quant', required=True,
                               ondelete='cascade',
                               domain=[('product_id.type', '=', 'product')])

    init_value = fields.Float('Value from receipt', readonly=True)

    old_value = fields.Float('Previous value',
                             help='Shows the previous value of the quant',
                             readonly=True)

    new_value = fields.Float('New Value',
                             help="Enter the new value you wish to assign to the Quant.",
                             digits=dp.get_precision('Product Price'),
                             copy=False)

    date = fields.Date('Date', related='revaluation_id.date')
    mentor_rates = fields.Integer()


    @api.onchange('quant_id')
    def onchange_quant_id(self):
        quant = self.quant_id

        if not quant.init_value:
            init_value = quant.inventory_value
        else:
            init_value = quant.init_value
        ajust = init_value * self.revaluation_id.percent / 100.0
        if self.revaluation_id.type == 'reduction':
            ajust = -1 * ajust
        new_value = quant.inventory_value + ajust
        self.product_id = quant.product_id
        self.init_value = init_value
        self.old_value = quant.inventory_value
        self.new_value = new_value


        # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
