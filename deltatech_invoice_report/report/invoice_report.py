# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class account_invoice_report(models.Model):
    _inherit = 'account.invoice.report'


    state_id = fields.Many2one("res.country.state", string='Region', readonly=True )
    supplier_id = fields.Many2one('res.partner', string='Default Supplier', readonly=True)

    def _select(self):
        return  super(account_invoice_report, self)._select() + ", sub.state_id,    sub.supplier_id"

    def _from(self):
        return  super(account_invoice_report, self)._from() + """
         LEFT JOIN ( select product_tmpl_id, min(name) as name from product_supplierinfo group by product_tmpl_id ) supplier ON pt.id = supplier.product_tmpl_id  
        """

    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", partner.state_id,   supplier.name as supplier_id"

    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + ", partner.state_id,     supplier.name "


