# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details



 
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

 
 


class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    in_rates = fields.Boolean(string="In Rates", compute="_compute_in_rates", store=True)


    @api.multi
    def view_rate(self):
        action = self.env.ref('deltatech_payment_term.action_account_moves_sale').read()[0]
        action['domain'] = "['|',('invoice_id','=',"+str(self.id)+" ),('name','ilike','"+str(self.number)+"')]"
        return action          

    @api.multi
    @api.depends('payment_term_id')
    def _compute_in_rates(self):
        for invoice in self:
            in_rates = False
            if invoice.payment_term_id:
                if len(invoice.payment_term_id.line_ids) > 1:
                    in_rates = True

            invoice.in_rates = in_rates
