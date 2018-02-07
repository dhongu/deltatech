# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import time
import json
import locale
from openerp.osv import expression

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


class dashboard_graph(models.Model):
    _name = 'dashboard.graph'
    _description = "Dashboard Graph"

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    color = fields.Selection([('purple', 'purple'), ('blue', 'blue'), ('green', 'green'),
                              ('orange', 'orange'), ('red', 'red')], string='Color')

    series_ids = fields.One2many('dashboard.graph.series', 'dashboard_graph_id', string='Series')
    col = fields.Selection([('2', '2'), ('3', '3'), ('4', '4'),
                            ('5', '5'), ('6', '6'), ('12', '12')], string="Width in columns",
                           default='6')

    type = fields.Selection([('pie', 'Pie'), ('line', 'Line'), ('bar', 'Bar')])
    time_series = fields.Boolean(string="Time series")
    no_group = fields.Boolean('No group')
    footer_symbol = fields.Char(string='Mini Symbol')
    footer_symbol_type = fields.Selection([('fa', 'Font Awesome'), ('mi', 'Material Icons')], string="Mini symbol type")
    footer_text = fields.Char(string='Footer')

    @api.multi
    def get_data_pie(self):
        self.ensure_one()
        res = {
            'labels': [],
            'series': []
        }
        labels = []
        graph_series = []
        for series in self.series_ids:
            records = series.get_records()
            for record in records:
                label_value = record[series.label_field_id.name]
                if type(label_value) == tuple:
                    label_value = label_value[1]
                labels += [label_value]
                value = record[series.value_field_id.name]
                graph_series += [value]
            res['series'] = graph_series
            res['labels'] = labels
            break
        return json.dumps(res)

    @api.multi
    def get_data(self):
        self.ensure_one()
        res = {'labels': [], 'series': []}

        labels = []

        y_values = {}
        for series in self.series_ids:
            field_name = series.label_field_id.name
            if self.time_series and not self.no_group:
                field_name = field_name + ':day'

            y_values[series.id] = {}
            records = series.get_records()

            for record in records:
                label_value = record[field_name]
                if type(label_value) == tuple:
                    label_value = label_value[1]
                if label_value not in labels:
                    labels += [label_value]
                value = record[series.value_field_id.name]
                if label_value in y_values[series.id]:
                    y_values[series.id][label_value] += value
                else:
                    y_values[series.id][label_value] = value

        labels = sorted(labels)

        for series in self.series_ids:
            graph_series = {'name': series.name,
                            'data': []}
            for label in labels:
                value = y_values[series.id].get(label, None)
                if value and series.negative:
                    value = -1 * value
                if self.time_series and not self.no_group:
                    locale.setlocale(locale.LC_TIME, ('ro', 'UTF-8'))

                    label = datetime.strptime(label.replace('.', '').replace('sept', 'sep'), '%d %b %Y')

                graph_series['data'] += [{'x': label, 'y': value}]
            res['series'] += [graph_series]

        res['labels'] = labels
        return json.dumps(res, cls=Encoder)


class dashboard_graph_series(models.Model):
    _name = 'dashboard.graph.series'

    dashboard_graph_id = fields.Many2one('dashboard.graph')
    name = fields.Char(string='Name')
    model_id = fields.Many2one('ir.model', 'Model', required=True)
    domain = fields.Text(default='[]')
    negative = fields.Boolean('Negative')
    date_field_id = fields.Many2one('ir.model.fields', string='Date Field',
                                    domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]")
    value_field_id = fields.Many2one('ir.model.fields', string='Value Field',
                                     domain="[('model_id', '=', model_id), ('ttype', 'in', ['float', 'integer'])]")
    label_field_id = fields.Many2one('ir.model.fields', string='Label Field', domain="[('model_id', '=', model_id)]")

    action_id = fields.Many2one('ir.actions.act_window', 'Action')
    top = fields.Integer()

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
        if self.dashboard_graph_id.time_series and not self.dashboard_graph_id.no_group:
            group_by = [self.label_field_id.name + ':day']
        else:
            group_by = [self.label_field_id.name]
        my_fields = [self.label_field_id.name, self.value_field_id.name]
        order_by = self.label_field_id.name

        if self.dashboard_graph_id.no_group:
            record_ids = model.search(domain, order=order_by, limit=self.top)
            records = record_ids.read(fields=my_fields)
        else:
            records = model.read_group(domain=domain, fields=my_fields, groupby=group_by, limit=self.top,
                                       orderby=order_by, lazy=False)

        return records
