# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Deltatech All Rights Reserved
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
from openerp.exceptions import except_orm, Warning, RedirectWarning, ValidationError
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import time
from openerp.osv import expression


from collections import OrderedDict


def median(vals):
    # https://docs.python.org/3/library/statistics.html#statistics.median
    # TODO : refactor, using statistics.median when Odoo will be available
    #  in Python 3.4
    even = (0 if len(vals) % 2 else 1) + 1
    half = (len(vals) - 1) / 2
    return sum(sorted(vals)[half:half + even]) / float(even)


FIELD_FUNCTIONS = OrderedDict([
    ('count', {
        'name': 'Count',
        'func': False,  # its hardcoded in _compute_data
        'help': _('Number of records')}),
    ('min', {
        'name': 'Minimum',
        'func': min,
        'help': _("Minimum value of '%s'")}),
    ('max', {
        'name': 'Maximum',
        'func': max,
        'help': _("Maximum value of '%s'")}),
    ('sum', {
        'name': 'Sum',
        'func': sum,
        'help': _("Total value of '%s'")}),
    ('avg', {
        'name': 'Average',
        'func': lambda vals: sum(vals) / len(vals),
        'help': _("Minimum value of '%s'")}),
    ('median', {
        'name': 'Median',
        'func': median,
        'help': _("Median value of '%s'")}),
])

FIELD_FUNCTION_SELECTION = [
    (k, FIELD_FUNCTIONS[k].get('name')) for k in FIELD_FUNCTIONS]


class dashboard_tile(models.Model):
    _name = 'dashboard.tile'
    _description = "Dashboard Tile"
    _order = 'sequence,id'

    def _get_eval_context(self):
        def _context_today():
            return fields.Date.from_string(fields.Date.context_today(self))

        context = self.env.context.copy()
        context.update({
            'time': time,
            'datetime': datetime,
            'relativedelta': relativedelta,
            'context_today': _context_today,
            'current_date': fields.Date.today(),
        })
        return context

    name = fields.Char(string='Name')
    symbol = fields.Char(string='Symbol')
    symbol_type = fields.Selection([('fa', 'Font Awesome'), ('mi', 'Material Icons')])
    color = fields.Selection([('purple', 'purple'), ('blue', 'blue'), ('green', 'green'),
                              ('orange', 'orange'), ('red', 'red')], string='Color')

    footer_symbol = fields.Char(string='Mini Symbol')
    footer_symbol_type = fields.Selection([('fa', 'Font Awesome'), ('mi', 'Material Icons')], string="Mini symbol type")
    footer_text = fields.Char(string='Footer')

    model_id = fields.Many2one('ir.model', 'Model', required=True)
    domain = fields.Text(default='[]')
    no_group = fields.Boolean('No group')
    action_id = fields.Many2one('ir.actions.act_window', 'Action')

    sequence = fields.Integer(string='Sequence')


    date_field_id = fields.Many2one('ir.model.fields', string='Date Field',
                                    domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]")
    # Primary Value
    primary_function = fields.Selection(FIELD_FUNCTION_SELECTION, string='Function', default='count')
    primary_field_id = fields.Many2one('ir.model.fields', string='Field',
                                       domain="[('model_id', '=', model_id), ('ttype', 'in', ['float', 'integer'])]")
    primary_negative = fields.Boolean('Negative')

    primary_value = fields.Char(string='Value', compute='_compute_data')

    # Secondary Value
    secondary_function = fields.Selection(FIELD_FUNCTION_SELECTION, string='Function', default='count')
    secondary_field_id = fields.Many2one('ir.model.fields', string='Field',
                                         domain="[('model_id', '=', model_id), ('ttype', 'in', ['float', 'integer'])]")
    secondary_negative = fields.Boolean('Negative')

    secondary_value = fields.Char(string='Value', compute='_compute_data')

    operator = fields.Selection([('+', '+'), ('-', '-'), ('*', '*'), ('/', '/')], default='+', required=True)

    total_value = fields.Float(string='Value', compute='_compute_data')

    error = fields.Char(string='Error Details', compute='_compute_data')


    @api.one
    def _compute_data(self):
        try:
            model = self.env[self.model_id.model]
            eval_context = self._get_eval_context()
            domain = self.domain or '[]'
            domain = eval(domain, eval_context)
            if 'date_range' in self.env.context and self.date_field_id:
                start = self.env.context['date_range']['start']
                end = self.env.context['date_range']['end']
                date_domain = [(self.date_field_id.name, '>=', start),
                               (self.date_field_id.name, '<=', end)]
                domain = expression.AND([domain, date_domain])

            field_name = self.primary_field_id.name
            if self.no_group:
                record = model.search(domain, limit=1)
                self.primary_value = record[self.primary_field_id.name]
                if self.secondary_field_id:
                    self.secondary_value = record[self.secondary_field_id.name]
            else:
                if self.primary_function == 'sum':
                    records = model.read_group(domain=domain, fields=[field_name], groupby=[])
                    value = records and records[0][field_name] or 0.0
                    if self.primary_negative:
                        value = -1 * value
                    self.primary_value = value
                elif self.primary_function == 'count':
                    value = model.search_count(domain)
                    self.primary_value = value
                elif self.primary_function == 'min':
                    records = model.read_group(domain=domain, fields=[field_name], groupby=[field_name],
                                               orderby=field_name, limit=1)
                    value = records and records[0][field_name] or 0.0
                    if self.primary_negative:
                        value = -1 * value
                    self.primary_value = value
                elif self.primary_function == 'max':
                    records = model.read_group(domain=domain, fields=[field_name], groupby=[field_name],
                                               orderby=field_name + ' DESC', limit=1)
                    value = records and records[0][field_name] or 0.0
                    if self.primary_negative:
                        value = -1 * value
                    self.primary_value = value

                if self.secondary_field_id:
                    field_name = self.secondary_field_id.name

                    if self.secondary_function == 'sum':
                        records = model.read_group(domain=domain, fields=[field_name], groupby=[])
                        value = records and records[0][field_name] or 0.0
                        if self.secondary_negative:
                            value = -1 * value
                        self.secondary_value = value
                    elif self.secondary_function == 'count':
                        value = model.search_count(domain)
                        self.secondary_value = value
                    elif self.secondary_function == 'min':
                        records = model.read_group(domain=domain, fields=[field_name], groupby=[field_name],
                                                   orderby=field_name, limit=1)
                        value = records and records[0][field_name] or 0.0
                        if self.secondary_negative:
                            value = -1 * value
                        self.secondary_value = value
                    elif self.secondary_function == 'max':
                        records = model.read_group(domain=domain, fields=[field_name], groupby=[field_name],
                                                   orderby=field_name + ' DESC', limit=1)
                        value = records and records[0][field_name] or 0.0
                        if self.secondary_negative:
                            value = -1 * value
                        self.secondary_value = value
                else:
                    self.secondary_value = 0.0

            total = '%s %s %s' % (self.primary_value, self.operator, self.secondary_value)
            self.total_value = eval(total)

        except Exception as e:
            self.primary_value = 'ERR! %s' % str(e)
            self.error = str(e)
            print str(e)
            return

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.primary_field_id = False

    @api.onchange('primary_function')
    def _onchange_function(self):
        if self.primary_function in [False, 'count']:
            self.primary_field_id = False

    # Action methods
    @api.multi
    def open_link(self):
        res = {
            'name': self.name,
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': [False],
            'res_model': self.model_id.model,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'nodestroy': True,
            'target': 'current',
            'domain': self.domain,
        }
        if self.action_id:
            res.update(self.action_id.read(['view_type', 'view_mode', 'type'])[0])
        return res

    @api.model
    def add(self, vals):
        if 'model_id' in vals and not vals['model_id'].isdigit():
            # need to replace model_name with its id
            vals['model_id'] = self.env['ir.model'].search(
                [('model', '=', vals['model_id'])]).id
        self.create(vals)
