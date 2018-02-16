# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

class account_invoice_report(models.Model):
    _inherit = 'account.invoice.report'


    state_id = fields.Many2one("res.country.state", string='Region', readonly=True ) 
    invoice_id = fields.Many2one('account.invoice', string='Invoice', readonly=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', readonly=True)

    def _select(self):
        return  super(account_invoice_report, self)._select() + ", sub.state_id,  sub.invoice_id, sub.supplier_id"

    def _from(self):
        return  super(account_invoice_report, self)._from() + " LEFT JOIN product_supplierinfo supplier ON pt.id = supplier.product_tmpl_id"

    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", partner.state_id,  ail.invoice_id, supplier.name as supplier_id"

    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + ", partner.state_id,  ail.invoice_id,  supplier.name "

    def init(self, cr):
        super(account_invoice_report, self).init(cr)
