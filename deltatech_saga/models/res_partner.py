# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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
#
##############################################################################


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
import math


class res_partner(models.Model):
    _inherit = "res.partner"

    ref_customer = fields.Char(string="Code Customer SAGA", size=5)
    ref_supplier = fields.Char(string="Code Supplier SAGA", size=5)

    @api.model
    def create(self, vals):
        if ('ref_customer' not in vals) or (vals.get('ref_customer') in ('/', False)):
            if vals.get('customer', False):
                sequence = self.env.ref('deltatech_saga.sequence_ref_customer')
                if sequence:
                    vals['ref_customer'] = self.env['ir.sequence'].next_by_id(sequence.id)

        if ('ref_supplier' not in vals) or (vals.get('ref_supplier') in ('/', False)):
            if vals.get('supplier', False):
                sequence = self.env.ref('deltatech_saga.sequence_ref_supplier')
                if sequence:
                    vals['ref_supplier'] = self.env['ir.sequence'].next_by_id(sequence.id)
        return super(res_partner, self).create(vals)

    @api.multi
    def write(self, vals):
        if ('ref_customer' in vals) and (vals.get('ref_customer' == '/')):
            self.ensure_one()
            if self.customer:
                sequence = self.env.ref('deltatech_saga.sequence_ref_customer')
                if sequence:
                    vals['ref_customer'] = self.env['ir.sequence'].next_by_id(sequence.id)

        if ('ref_supplier' in vals) and (vals.get('ref_supplier' == '/')):
            self.ensure_one()
            if self.supplier:
                sequence = self.env.ref('deltatech_saga.sequence_ref_supplier')
                if sequence:
                    vals['ref_supplier'] = self.env['ir.sequence'].next_by_id(sequence.id)

        return super(res_partner, self).write(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
