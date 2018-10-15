#-*- coding:utf-8 -*-
from openerp import models, api, _
from openerp.exceptions import Warning


class sale_order(models.Model):
    _inherit = "sale.order"

    @api.one
    def action_wait(self):
        self.check_limit()
        return super(sale_order, self).action_wait()

    @api.one
    def check_limit(self):

        if not self.partner_id.credit_limit:
            return True
        # We sum from all the sale orders that are aproved, the sale order
        # lines that are not yet invoiced
        
        domain = [('order_id.partner_id', '=', self.partner_id.id),
                  ('invoiced', '=', False),
                  ('order_id.state', 'not in', ['draft', 'cancel', 'sent'])]
        
        order_lines = self.env['sale.order.line'].search(domain)
        
        none_invoiced_amount = self.currency_id.compute(self.amount_total, self.env.user.company_id.currency_id)
        
         
        
        # la liniile astea mai trebuie adaugat si TVA-ul
        for line in order_lines:
            taxes = line.tax_id.compute_all(line.price_subtotal,1,line.product_id,line.order_id.partner_id)
            none_invoiced_amount += line.order_id.currency_id.compute(taxes['total_included'],self.env.user.company_id.currency_id)

        

        # We sum from all the invoices that are in draft the total amount
        domain = [  ('partner_id', '=', self.partner_id.id), ('state', '=', 'draft')]
        draft_invoices = self.env['account.invoice'].search(domain)
        draft_invoices_amount = 0.0
        
        for invoice in  draft_invoices:
            draft_invoices_amount += invoice.currency_id.compute(invoice.amount_total,self.env.user.company_id.currency_id)
        
        print self.partner_id.credit_limit ,   self.partner_id.credit ,   none_invoiced_amount , draft_invoices_amount

        available_credit = self.partner_id.credit_limit -   self.partner_id.credit -   none_invoiced_amount - draft_invoices_amount

        if available_credit < 0:
            
            msg = 'Depasire limita de credit cu %s' % str(abs(available_credit))
            raise Warning(_(msg))
            
        return True
