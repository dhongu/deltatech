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
    action_id = fields.Many2one('ir.actions.act_window', 'Action')

    # Primary Value
    primary_function = fields.Selection(FIELD_FUNCTION_SELECTION, string='Function', default='count')
    primary_field_id = fields.Many2one('ir.model.fields', string='Field',
                                       domain="[('model_id', '=', model_id), ('ttype', 'in', ['float', 'integer'])]")
    primary_negative = fields.Boolean('Negative')
    primary_format = fields.Char(string='Format',
                                 help='Python Format String valid with str.format()\n'
                                      'ie: \'{:,} Kgs\' will output \'1,000 Kgs\' if value is 1000.')
    primary_value = fields.Char(string='Value', compute='_compute_data')
    primary_helper = fields.Char(string='Helper', compute='_compute_helper')

    # Secondary Value
    secondary_function = fields.Selection(FIELD_FUNCTION_SELECTION, string='Secondary Function')
    secondary_field_id = fields.Many2one('ir.model.fields', string='Secondary Field',
                                         domain="[('model_id', '=', model_id),  ('ttype', 'in', ['float', 'integer'])]")
    secondary_negative = fields.Boolean('Negative')
    secondary_format = fields.Char(string='Secondary Format',
                                   help='Python Format String valid with str.format()\n'
                                        'ie: \'{:,} Kgs\' will output \'1,000 Kgs\' if value is 1000.')
    secondary_value = fields.Char(string='Secondary Value', compute='_compute_data')
    secondary_helper = fields.Char(string='Secondary Helper', compute='_compute_helper')

    error = fields.Char(string='Error Details', compute='_compute_data')

    @api.one
    def _compute_data(self):

        model = self.env[self.model_id.model]
        eval_context = self._get_eval_context()
        domain = self.domain or '[]'
        try:
            count = model.search_count(eval(domain, eval_context))
        except Exception as e:
            self.primary_value = self.secondary_value = 'ERR!'
            self.error = str(e)
            return
        if any([self.primary_function and self.primary_function != 'count',
                self.secondary_function and self.secondary_function != 'count'
                ]):
            records = model.search(eval(domain, eval_context))
        for f in ['primary_', 'secondary_']:
            f_function = f + 'function'
            f_field_id = f + 'field_id'
            f_format = f + 'format'
            f_value = f + 'value'
            f_negative = f + 'negative'
            value = 0
            if self[f_function] == 'count':
                value = count
            elif self[f_function]:
                func = FIELD_FUNCTIONS[self[f_function]]['func']
                if func and self[f_field_id] and count:
                    vals = [x[self[f_field_id].name] for x in records]
                    value = func(vals)
            if self[f_negative]:
                value = -1 * value
            if self[f_function]:
                try:
                    self[f_value] = (self[f_format] or '{:,}').format(value)
                except Exception as e:
                    self[f_value] = 'F_ERR!'
                    self.error = str(e)
                    return
            else:
                self[f_value] = False

    @api.one
    @api.onchange('primary_function', 'primary_field_id', 'secondary_function', 'secondary_field_id')
    def _compute_helper(self):
        for f in ['primary_', 'secondary_']:
            f_function = f + 'function'
            f_field_id = f + 'field_id'
            f_helper = f + 'helper'
            self[f_helper] = ''
            field_func = FIELD_FUNCTIONS.get(self[f_function], {})
            help = field_func.get('help', False)
            if help:
                if self[f_function] != 'count' and self[f_field_id]:
                    desc = self[f_field_id].field_description
                    self[f_helper] = help % desc
                else:
                    self[f_helper] = help

    # Constraints and onchanges
    @api.one
    @api.constrains('model_id', 'primary_field_id', 'secondary_field_id')
    def _check_model_id_field_id(self):
        if any([self.primary_field_id and self.primary_field_id.model_id.id != self.model_id.id,
                self.secondary_field_id and self.secondary_field_id.model_id.id != self.model_id.id
                ]):
            raise ValidationError(
                _("Please select a field from the selected model."))

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.primary_field_id = False
        self.secondary_field_id = False

    @api.onchange('primary_function', 'secondary_function')
    def _onchange_function(self):
        if self.primary_function in [False, 'count']:
            self.primary_field_id = False
        if self.secondary_function in [False, 'count']:
            self.secondary_field_id = False

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
