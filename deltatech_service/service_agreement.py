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


class service_cycle(models.Model):
    _name = 'service.cycle'
    _description = "Cycle"

    name = fields.Char(string='Cycle', translate=True)
    value = fields.Integer(string='Value')
    unit = fields.Selection([('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')],
                            string='Unit Of Measure', help="Unit of Measure for Cycle.")

    @api.model
    def get_cyle(self):
        self.ensure_one()
        if self.unit == 'day':
            return timedelta(days=self.value)
        if self.unit == 'week':
            return timedelta(weeks=self.value)
        if self.unit == 'month':
            return relativedelta(months=+self.value)  # monthdelta(self.value)
        if self.unit == 'year':
            return relativedelta(years=+self.value)


class service_agreement(models.Model):
    _name = 'service.agreement'
    _description = "Service Agreement"

    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    name = fields.Char(string='Reference', index=True, default='/', readonly=True,
                       states={'draft': [('readonly', False)]}, copy=False)

    description = fields.Char(string='Description', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    # active = fields.Boolean(default=True)  # pentru a ascunde un contract
    date_agreement = fields.Date(string='Agreement Date', default=lambda *a: fields.Date.today(),
                                 readonly=True, states={'draft': [('readonly', False)]}, copy=False)

    final_date = fields.Date(string="Final Date", readonly=True, states={'draft': [('readonly', False)]}, copy=False)

    partner_id = fields.Many2one('res.partner', string='Partner',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]})

    agreement_line = fields.One2many('service.agreement.line', 'agreement_id', string='Agreement Lines',
                                     readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'In Progress'),
        ('closed', 'Terminated'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False)

    type_id = fields.Many2one('service.agreement.type', string='Type', readonly=True,
                              states={'draft': [('readonly', False)]})

    # interval de facturare

    # interval revizii

    # valoare contract ???

    display_name = fields.Char(compute='_compute_display_name')

    invoice_mode = fields.Selection([('none', 'Not defined'), ('service', 'Group by service'), ('detail', 'Detail')],
                                    string="Invoice Mode", default='none', readonly=True,
                                    states={'draft': [('readonly', False)]})

    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=_default_currency,
                                  domain=[('name', 'in', ['RON', 'EUR'])], readonly=True,
                                  states={'draft': [('readonly', False)]})

    cycle_id = fields.Many2one('service.cycle', string='Billing Cycle', required=True, readonly=True,
                               states={'draft': [('readonly', False)]})

    last_invoice_id = fields.Many2one('account.invoice', string='Last Invoice', compute="_compute_last_invoice_id")

    last_invoice_date = fields.Date(string='Last Invoice Date', compute="_compute_last_invoice_id",
                                    store=True,
                                    readonly=True, default="2000-01-01")

    invoice_day = fields.Integer(string='Invoice Day', readonly=True, states={'draft': [('readonly', False)]},
                                 help="""Day of the month, set -1 for the last day of the month.
                                 If it's positive, it gives the day of the month. Set 0 for net days .""")

    prepare_invoice_day = fields.Integer(string='Prepare Invoice Day', readonly=True,
                                         states={'draft': [('readonly', False)]}, default=-1,
                                         help="""Day of the month, set -1 for the last day of the month.
                                 If it's positive, it gives the day of the month. Set 0 for net days .""")

    next_date_invoice = fields.Date(string='Next Invoice Date', compute="_compute_last_invoice_id", store=True)

    total_invoiced = fields.Float(string="Total invoiced", readonly=True)
    total_consumption = fields.Float(string="Total consumption", readonly=True)
    total_costs = fields.Float(string="Total Cost", readonly=True)  # se va calcula din suma avizelor
    total_percent = fields.Float(string="Total percent", readonly=True)  # se va calcula (consum/factura)*100

    invoicing_status = fields.Selection(
        [('', 'N/A'), ('unmade', 'Unmade'), ('progress', 'In progress'), ('done', 'Done')],
        string="Invoicing Status", compute="_compute_invoicing_status", store=True)

    billing_automation = fields.Selection([('auto', 'Auto'), ('manual', 'Manual')],
                                          string="Billing automation", default='manual')

    notes = fields.Text(string='Notes')
    meter_reading_status = fields.Boolean(default=False, string="Readings done")
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
                              readonly=True,  states={'draft': [('readonly', False)]},
                              default=lambda self: self.env.user)

    @api.model
    def _needaction_domain_get(self):
        return [('invoicing_status', '!=', 'done')]

    @api.model
    def compute_invoicing_status(self):
        self._compute_invoicing_status()

    @api.model
    def compute_totals_sup(self):
        self.compute_totals()

    @api.model
    def clear_meter_readings(self):
        agreements = self.search([])
        for agreement in agreements:
            agreement.write({'meter_reading_status': False })

    @api.multi
    def _compute_invoicing_status(self):
        agreements = self
        if not agreements:
            agreements = self.search([('state', '=', 'open')])

        for agreement in agreements:
            next_date = date.today()
            if agreement.prepare_invoice_day < 0:
                next_first_date = next_date + relativedelta(day=1, months=0)
                next_date = next_first_date + relativedelta(days=agreement.prepare_invoice_day)
            if agreement.prepare_invoice_day > 0:
                next_date += relativedelta(day=agreement.prepare_invoice_day, months=0)

            if next_date > date.today():
                next_date += relativedelta(months=-1)

            next_date = fields.Date.to_string(next_date)

            invoicing_status = 'done'

            invoice = self.env['account.invoice'].search([('agreement_id', '=', agreement.id)],
                                                         order='date_invoice desc, id desc', limit=1)
            if not invoice:
                invoicing_status = 'unmade'
            else:
                if not (invoice.date_invoice >= next_date):
                    invoicing_status = 'unmade'
                else:
                    if invoice.state in ['draft']:
                        invoicing_status = 'progress'

            agreement.write({'invoicing_status': invoicing_status, })
            agreement._compute_last_invoice_id()

    @api.multi
    def compute_totals(self):
        agreements = self
        if not agreements:
            agreements = self.search([('state', '=', 'open')])
        for agreement in agreements:
            total_consumption = 0.0
            total_invoiced = 0.0
            total_costs = 0.0
            total_percent = 0.0
            consumptions = self.env['service.consumption'].search([('agreement_id', '=', agreement.id)])
            invoices = self.env['account.invoice'].search([('agreement_id', '=', agreement.id)])
            for consumption in consumptions:
                if consumption.state == 'done':
                    total_consumption += consumption.currency_id.compute(consumption.price_unit * consumption.quantity,
                                                                         self.env.user.company_id.currency_id)
                    # invoices |= consumption.invoice_id
            for invoice in invoices:
                if invoice.state in ['open', 'paid']:
                    total_invoiced += invoice.amount_untaxed

            pickings = self.env['stock.picking'].search([('agreement_id', '=', agreement.id), ('state', '=', 'done')])
            for picking in pickings:
                for move in picking.move_lines:
                    move_value = 0.0
                    for quant in move.quant_ids:
                        move_value += quant.cost * quant.qty
                    if move.location_id.usage == 'internal':
                        total_costs += move_value
                    else:
                        total_costs -= move_value

            if total_costs > 0.0:
                total_percent = (total_invoiced/total_costs)*100


            agreement.write({'total_invoiced': total_invoiced,
                             'total_consumption': total_consumption,
                             'total_costs': total_costs,
                             'total_percent':total_percent
                             })

    # TODO: de legat acest contract la un cont analitic ...
    @api.one
    def _compute_last_invoice_id(self):
        self.last_invoice_id = self.env['account.invoice'].search(
            [('agreement_id', '=', self.id), ('state', 'in', ['open', 'paid'])],
            order='date_invoice desc, id desc', limit=1)

        if self.last_invoice_id:
            date_invoice = self.last_invoice_id.date_invoice
            self.last_invoice_date = self.last_invoice_id.date_invoice
        else:
            date_invoice = self.date_agreement

        if date_invoice and self.cycle_id:
            next_date = fields.Date.from_string(date_invoice) + self.cycle_id.get_cyle()
            if self.invoice_day < 0:
                next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                next_date = next_first_date + relativedelta(days=self.invoice_day)
            if self.invoice_day > 0:
                next_date += relativedelta(day=self.invoice_day, months=0)

            self.next_date_invoice = fields.Date.to_string(next_date)

    @api.one
    @api.depends('name', 'date_agreement')
    def _compute_display_name(self):
        if self.date_agreement:
            self.display_name = self.name + ' / ' + self.date_agreement
        else:
            self.display_name = self.name

    @api.model
    def create(self, vals):
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence_agreement = self.env.ref('deltatech_service.sequence_agreement')
            if sequence_agreement:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence_agreement.id)
        return super(service_agreement, self).create(vals)

    @api.multi
    def contract_close(self):
        return self.write({'state': 'closed'})

    @api.multi
    def contract_open(self):
        return self.write({'state': 'open'})

    @api.multi
    def contract_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for item in self:
            if item.state not in ('draft'):
                raise Warning(_('You cannot delete a service agreement which is not draft.'))
        return super(service_agreement, self).unlink()

    @api.model
    def get_link(self, model):
        for model_id, model_name in model.name_get():
            link = "<a href='#id=%s&model=%s'>%s</a>" % (str(model_id), model._name, model_name)
        return link

    @api.model
    def send_mail_todo_today(self):

        data1 = (date.today() + relativedelta(days=-2)).strftime('%Y-%m-%d')
        data2 = (date.today() + relativedelta(days=2)).strftime('%Y-%m-%d')
        agreements = self.search([('state', '=', 'open'),
                                  ('next_date_invoice', '>=', data1),
                                  ('next_date_invoice', '<=', data2)
                                  ])

        for agreement in agreements:
            follower = agreement.message_follower_ids
            msg = _('Please make invoice for agreement %s') % agreement.name
            print follower
            message = self.env['mail.message'].with_context({'default_starred': True}).create({
                'model': 'service.agreement',
                'res_id': agreement.id,
                'record_name': agreement.name_get()[0][1],
                'email_from': self.env['mail.message']._get_default_from(),
                'reply_to': self.env['mail.message']._get_default_from(),

                'subject': _('To invoice'),
                'body': msg,

                'message_id': self.env['mail.message']._get_message_id({'no_auto_thread': True}),
                'partner_ids': [(4, id) for id in follower.ids],
                # 'notified_partner_ids': [(4, id) for id in new_follower_ids]
            })

    @api.model
    def make_billing_automation(self):
        print "Faturare automata"
        agreements = self.search([('billing_automation', '=', 'auto')])
        period = self.env['account.period'].find()
        consumptions = self.env['service.consumption'].search(
            [('period_id', '=', period.id), ('agreement_id', 'in', agreements.ids)])
        for consumption in consumptions:
            agreements = agreements - consumption.agreement_id
        if agreements:
            wizard_preparation = self.env['service.billing.preparation'].with_context(active_ids=agreements.ids).create(
                {})
            res = wizard_preparation.do_billing_preparation()
            if res:
                wizard_billing = self.env['service.billing'].with_context(active_ids=res['consumption_ids']).create({})
                wizard_billing.do_billing()

    @api.multi
    def get_counters(self):
        histories = self.env['service.equipment.history'].search([('agreement_id','=',self.id)])
        equipment_ids = []
        history_ids = []
        for history in histories:
            history_ids+=[history.id]
            if history.equipment_id.id not in equipment_ids:
                equipment_ids+=[history.equipment_id.id]
        #cautare readings care au echipamentul care a fost in contract si history-ul cu agreement_id-ul potrivit
        readings = self.env['service.meter.reading'].search([('equipment_id', 'in', equipment_ids), ('equipment_history_id', 'in', history_ids)],order="date")
        return readings

    @api.multi
    def get_counters_ea(self,address_id):
        history_ids = []
        histories = self.env['service.equipment.history'].search([('agreement_id', '=', self.id),('address_id','=',address_id)])
        for history in histories:
            history_ids+=[history.id]
        readings = self.env['service.meter.reading'].search([('equipment_history_id', 'in', history_ids)], order="date")
        return readings

    @api.multi
    def picking_button(self):
        pickings = self.env['stock.picking'].search([('agreement_id', '=', self.id)])
        context = {'default_agreement_id': self.id,
                   'default_picking_type_code': 'outgoing',
                   'default_picking_type_id': self.env.ref('stock.picking_type_outgoing_not2binvoiced').id}

        return {
            'domain': "[('id','in', [" + ','.join(map(str, pickings.ids)) + "])]",
            'name': _('Delivery for service'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window'
        }

class service_agreement_type(models.Model):
    _name = 'service.agreement.type'
    _description = "Service Agreement Type"
    name = fields.Char(string='Type', translate=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)


class service_agreement_line(models.Model):
    _name = 'service.agreement.line'
    _description = "Service Agreement Line"
    _order = "sequence,id desc,agreement_id"

    sequence = fields.Integer(string='Sequence', default=1, help="Gives the sequence of this line when displaying the agreement.")
    agreement_id = fields.Many2one('service.agreement', string='Contract Services', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Service', ondelete='set null',
                                 domain=[('type', '=', 'service')])
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1)
    quantity_free = fields.Float(string='Quantity Free', digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', ondelete='set null')
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Service Price'), default=1)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True,
                                  domain=[('name', 'in', ['RON', 'EUR'])])
    active = fields.Boolean(default=True)  # pentru a ascunde liniile din contract care nu
    invoice_description = fields.Char(string='Invoice Description')

    @api.onchange('product_id')
    def onchange_product_id(self):

        self.uom_id = self.product_id.uom_id
        price_unit = self.product_id.list_price

        price_type = self.env['product.price.type'].search([('field', '=', 'list_price')])
        if price_type:
            list_price_currency_id = price_type.currency_id
        else:
            list_price_currency_id = self.env.user.company_id.currency_id

        self.price_unit = list_price_currency_id.compute(price_unit, self.currency_id)

    @api.model
    def get_value_for_consumption(self):
        cons_value = {
            'product_id': self.product_id.id,
            'quantity': self.quantity,
            'price_unit': self.price_unit,
            'currency_id': self.currency_id.id
        }
        return cons_value

    @api.model
    def after_create_consumption(self, consumption):
        return [consumption.id]


# e posibil ca o factura sa contina mai multe contracte 
class account_invoice(models.Model):
    _inherit = 'account.invoice'
    agreement_id = fields.Many2one('service.agreement', string='Service Agreement',
                                   related='invoice_line.agreement_line_id.agreement_id', store=True)

    @api.multi
    def action_cancel(self):
        res = super(account_invoice, self).action_cancel()
        consumptions = self.env['service.consumption'].search([('invoice_id', 'in', self.ids)])
        if consumptions:
            consumptions.write({'state': 'draft',
                                # 'invoice_id':False  totusi sa pastrez id poate se revalideaza factura
                                })
            for consumption in consumptions:
                consumption.agreement_id.compute_totals()
        return res

    @api.multi
    def unlink(self):
        consumptions = self.env['service.consumption'].search([('invoice_id', 'in', self.ids)])
        if consumptions:
            consumptions.write({'state': 'draft'})
            for consumption in consumptions:
                consumption.agreement_id.compute_totals()
        return super(account_invoice, self).unlink()

    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        agreements = self.env['service.agreement']
        for invoice in self:
            for line in invoice.invoice_line:
                agreements |= line.agreement_line_id.agreement_id
        agreements.compute_totals()
        consumptions = self.env['service.consumption'].search([('invoice_id', 'in', self.ids)])
        if consumptions:
            consumptions.write({'state': 'done'})
        return res

    @api.multi
    def get_counters(self):
        readings = []
        c_reading_ids = []
        consumptions = self.env['service.consumption'].search([('invoice_id', 'in', self.ids)])
        for consumption in consumptions:
            c_reading_ids += [consumption.id]
        readings = self.env['service.meter.reading'].search([('consumption_id','in',c_reading_ids)])
        return readings

class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'
    agreement_line_id = fields.Many2one('service.agreement.line', string='Service Agreement Line')
