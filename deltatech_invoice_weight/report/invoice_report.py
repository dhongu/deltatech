# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
# import odoo.addons.decimal_precision as dp

class account_invoice_report(models.Model):
    _inherit = 'account.invoice.report'

    weight = fields.Float('Weight')
    weight_net = fields.Float('Net Weight')
    weight_package = fields.Float('Package Weight')
    
    def _select(self):
        return  super(account_invoice_report, self)._select() + ", sub.weight,    sub.weight_net, sub.weight_package "

    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", ai.weight as weight,    ai.weight_net as weight_net,    ai.weight_package as weight_package "

   


