# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import time
from openerp.osv import expression

class dashboard_table(models.Model):
    _name = 'dashboard.table'
    _description = "Dashboard table"
    _order = 'sequence,id'

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    color = fields.Selection([('purple', 'purple'), ('blue', 'blue'), ('green', 'green'),
                              ('orange', 'orange'), ('red', 'red')], string='Color')

    model_id = fields.Many2one('ir.model', 'Model', required=True)
    domain = fields.Text(default='[]')
    action_id = fields.Many2one('ir.actions.act_window', 'Action')
    date_field_id = fields.Many2one('ir.model.fields', string='Date Field',
                                    domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]")

    col = fields.Selection([('2', '2'), ('3', '3'), ('4', '4'),
                            ('5', '5'), ('6', '6'), ('12', '12')], string="Width in columns", default='6')
    order_by = fields.Char('Order by')
    field_ids = fields.One2many('dashboard.table.fields', 'dashboard_table_id', string='Fields')

    top = fields.Integer()
    sequence = fields.Integer(string='Sequence')

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

    @api.multi
    def get_records(self):
        self.ensure_one()
        model = self.env[self.model_id.model]
        eval_context = self._get_eval_context()
        domain = eval(self.domain, eval_context)
        if 'date_range' in self.env.context and self.date_field_id:
            start = self.env.context['date_range']['start']
            end = self.env.context['date_range']['end']
            date_domain = [(self.date_field_id.name, '>=', start),
                           (self.date_field_id.name, '<=', end)]
            domain = expression.AND([domain, date_domain])
        # records = model.search(eval(domain, eval_context), order=self.order_by, limit=self.top)
        group_by = []
        my_fields = []
        for f in self.field_ids:
            my_fields += [f.field_id.name]
            if f.func == 'group':
                group_by += [f.field_id.name]

        records = model.read_group(domain=domain, fields=my_fields, groupby=group_by, limit=self.top,
                                   orderby=self.order_by, lazy=False)

        return records

    @api.model
    def get_field(self, record, field_name):
        value = record[field_name]
        if type(value) == tuple:
            value = value[1]
        return value


class dashboard_table_field(models.Model):
    _name = 'dashboard.table.fields'
    _description = "Dashboard table fields"
    _order = "dashboard_table_id,sequence,id"

    dashboard_table_id = fields.Many2one('dashboard.table')
    sequence = fields.Integer(string='Sequence')
    model_id = fields.Many2one('ir.model', 'Model', related='dashboard_table_id.model_id')
    field_id = fields.Many2one('ir.model.fields', string='Field', domain="[('model_id', '=', model_id)]")
    func = fields.Selection([('sum', 'Sum'), ('group', 'Group By')], string="Function")
