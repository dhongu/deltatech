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
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class commission_compute_total(models.TransientModel):
    _name = 'commission.compute.total'
    _description = "Compute commission total"

    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    item_ids = fields.One2many('commission.compute.total.line', 'total_id')

    @api.multi
    def do_compute(self):
        commission_user = self.env['commission.users']

        domain = [('date', '>=', self.from_date), ('date', '<=', self.to_date)]
        commissions = self.env["sale.margin.report"].read_group(domain=domain, fields=['user_id', 'commission'],
                                                                groupby=['user_id'])
        for item in commissions:
            self.env['commission.compute.total.line'].create(
                {'total_id': self.id, 'user_id': item['user_id'][0], 'commission': item['commission']})

        while self.item_ids.filtered(lambda r: not r.final):
            for item in self.item_ids.filtered(lambda r: not r.final):
                commission_user = self.env['commission.users'].search([('user_id', '=', item.user_id.id)])
                item.write({'final': True})
                if commission_user:
                    if  commission_user.manager_user_id:
                        item.write({'final': True})
                        self.env['commission.compute.total.line'].create({
                                'total_id': self.id,
                                'user_id': commission_user.manager_user_id.id,
                                'commission': item.commission * commission_user.manager_rate
                            })

        domain = [('total_id','=',self.id)]
        commissions = self.env["commission.compute.total.line"].read_group(domain=domain, fields=['user_id', 'commission'],
                                                                groupby=['user_id'])
        self.item_ids.unlink()
        for item in commissions:
            self.env['commission.compute.total.line'].create(
                {'total_id': self.id, 'user_id': item['user_id'][0], 'commission': item['commission']})

        return {
            'domain': "[('total_id','=', " + str(self.id)  + ")]",
            'name': _('Commission per saleman'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'commission.compute.total.line',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }


class commission_compute_total_line(models.TransientModel):
    _name = 'commission.compute.total.line'
    _description = "Compute commission total line"

    total_id = fields.Many2one('commission.compute.total')
    user_id = fields.Many2one('res.users', string='Salesperson', required=True)
    commission = fields.Float(string="Commission", default=0.0)
    final = fields.Boolean()



class commission_compute(models.TransientModel):
    _name = 'commission.compute'
    _description = "Compute commission"

    invoice_line_ids = fields.Many2many('sale.margin.report', 'commission_compute_inv_rel', 'compute_id',
                                        'invoice_line_id',
                                        string='Account invoice line')

    @api.model
    def default_get(self, fields):
        defaults = super(commission_compute, self).default_get(fields)

        active_ids = self.env.context.get('active_ids', False)

        if active_ids:
            domain = [('id', 'in', active_ids)]
        else:
            domain = [('state', '=', 'paid'), ('commission', '=', 0.0)]
        res = self.env['sale.margin.report'].search(domain)
        defaults['invoice_line_ids'] = [(6, 0, [rec.id for rec in res])]
        return defaults

    @api.multi
    def do_compute(self):
        res = []
        for line in self.invoice_line_ids:
            value = {'commission': line.commission_computed}
            # if line.purchase_price == 0 and line.product_id:
            #    value['purchase_price'] = line.product_id.standard_price

            line.write(value)
            res.append(line.id)
        return {
            'domain': "[('id','in', [" + ','.join(map(str, res)) + "])]",
            'name': _('Commission'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.margin.report',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
