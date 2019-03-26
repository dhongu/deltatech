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



from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta


class stock_location(models.Model):
    _inherit = "stock.location"

    user_id = fields.Many2one('res.users', string='Manager')


class required_order(models.Model):
    _name = 'required.order'
    _description = "Required Products Order"
    _inherit = 'mail.thread'



    name = fields.Char(string='Reference', index=True, readonly=True, states={'draft': [('readonly', False)]},
                       default=lambda self:  self.env['ir.sequence'].next_by_code('required.order'),
                       copy=False)
    date = fields.Date(string='Date', required=True, readonly=True, states={'draft': [('readonly', False)]},
                       default=fields.Date.today())

    state = fields.Selection([
        ('draft', 'Draft'),
        ('progress', 'Confirmed'),
        ('cancel', 'Canceled'),
        ('done', 'Done'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False)

    required_line = fields.One2many('required.order.line', 'required_id', string='Required Lines', readonly=True,
                                    states={'draft': [('readonly', False)]})
    date_planned = fields.Date(string='Scheduled Date', readonly=True, states={'draft': [('readonly', False)]})
    location_id = fields.Many2one('stock.location', required=True, string='Procurement Location', readonly=True,
                                  states={'draft': [('readonly', False)]})
    group_id = fields.Many2one('procurement.group', string='Procurement Group', readonly=True)

    route_id = fields.Many2one('stock.location.route', string='Route', readonly=True,
                               states={'draft': [('readonly', False)]})

    warehouse_id = fields.Many2one('stock.warehouse', required=True, string='Warehouse', readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   help="Warehouse to consider for the route selection")

    procurement_count = fields.Integer(string='Procurements', compute='_compute_procurement_count')
    comment = fields.Char(string='Comment')
    product_id = fields.Many2one('product.product', string='Product', related='required_line.product_id')

    @api.model
    def default_get(self, fields):
        defaults = super(required_order, self).default_get(fields)
        central_location = self.env.ref('stock.stock_location_stock')
        my_location = self.env['stock.location'].search([('user_id', '=', self.env.user.id),
                                                         ('id', '!=', central_location.id),
                                                         ('usage', '=', 'internal')
                                                         ], limit=1)

        if my_location:
            defaults['location_id'] = my_location.id
        else:
            defaults['location_id'] = central_location.id

        defaults['warehouse_id'] = self.env.ref('stock.warehouse0').id

        return defaults

    #    @api.onchange('warehouse_id')
    #    def onchange_warehouse_id(self):
    #        self.location_id = self.warehouse_id.lot_stock_id

    # todo: move to new api
    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'required.order'),
    }

    @api.multi
    def order_done(self):
        return self.write({'state': 'done'})

    @api.multi
    def order_confirm(self):
        for order in self:
            group = self.env['procurement.group'].sudo().create({'name': order.name})
            order.write({'group_id': group.id})
            procurement = order.required_line.sudo().create_procurement()
            if not self.date_planned:
                date_planned = self.date
                for line in order.required_line:
                    if line.date_planned > date_planned:
                        date_planned = line.date_planned
                order.write({'date_planned': date_planned})

        return self.write({'state': 'progress'})

    @api.multi
    def action_cancel(self):
        for order in self:
            is_cancel = True
            for line in order.required_line:
                line.procurement_id.cancel()

                # is_cancel = is_cancel and   (line.procurement_id.state == 'cancel')
            is_cancel = all(line.procurement_id.state == 'cancel' for line in order.required_line)
            if is_cancel:
                order.write({'state': 'cancel'})
            else:
                raise Warning(_('You cannot cancel a order with procurement not canceled '))

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise Warning(_('You cannot delete a order which is not draft or cancelled. '))
        return super(required_order, self).unlink()

    @api.multi
    def check_order_done(self):
        for order in self:
            is_done = True
            for line in order.required_line:
                if line.procurement_id.state != "done":
                    is_done = False
            if is_done:
                order.order_done()

    @api.depends('required_line.procurement_id')
    def _compute_procurement_count(self):
        value = 0
        procurements = self.env['procurement.order']
        for order in self:
            for line in order.required_line:
                procurements = procurements | line.procurement_id

        self.procurement_count = len(procurements)

    @api.multi
    def view_procurement(self):
        '''
        This function returns an action that display existing procurement of given purchase order ids.
        '''

        action = self.ref('procurement.procurement_action').read()[0]

        procurement_ids = []
        for order in self:
            for line in order.required_line:
                procurement_ids += [line.procurement_id.id]

        action['context'] = {}

        if len(procurement_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, procurement_ids)) + "])]"
        else:
            res = self.res('procurement.procurement_form_view').read()
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = procurement_ids and procurement_ids[0] or False
        return action




    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'progress':
            return 'deltatech_required.mt_order_confirmed'
        elif 'state' in init_values and self.state == 'done':
            return 'deltatech_required.mt_order_done'
        return super(required_order, self)._track_subtype(init_values)




class required_order_line(models.Model):
    _name = 'required.order.line'
    _description = "Required Products Order Line"

    required_id = fields.Many2one('required.order', string='Required Products Order', ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='set null')
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
    procurement_id = fields.Many2one('procurement.order', string='Procurement Order')
    note = fields.Char(string='Note')

    qty_available = fields.Float(related='product_id.qty_available', string='Quantity On Hand')
    virtual_available = fields.Float(related='product_id.virtual_available', string='Quantity Available')

    date_planned = fields.Datetime(string='Scheduled Date', readonly=True, states={'draft': [('readonly', False)]}
                                   , compute='_compute_date_planned', store=True)

    @api.depends('required_id.date', 'product_id')
    def _compute_date_planned(self):
        for line in self:
            supplierinfo = False

            for supplier in line.product_id.seller_ids:
                supplierinfo = supplier
                break

            supplier_delay = int(supplierinfo.delay) if supplierinfo else 0
            date_planned = fields.Date.from_string(line.required_id.date) + relativedelta(days=supplier_delay)
            date_planned = fields.Datetime.to_string(date_planned)
            if line.required_id.date_planned and line.required_id.date_planned > date_planned:
                date_planned = line.required_id.date_planned

            line.date_planned = date_planned

    @api.multi
    def create_procurement(self):
        procurement = self.env['procurement.order']
        for line in self:

            order = line.required_id
            values = {
                'name': line.note or line.product_id.name,
                'origin': order.name + ':' + order.location_id.name,
                'date_planned': line.date_planned,
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'warehouse_id': order.warehouse_id.id,
                'location_id': order.location_id.id,
                'group_id': order.group_id.id,
                'required_id': order.id,
            }

            if order.route_id:
                values['route_ids'] = [(6, 0, [order.route_id.id])]

            procurement = self.env['procurement.order'].create(values)
            procurement.run()
            if not procurement.rule_id:
                raise Warning(_('Role not found for product %s!') % line.product_id.name)

            line.write({'procurement_id': procurement.id})
        return procurement

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
