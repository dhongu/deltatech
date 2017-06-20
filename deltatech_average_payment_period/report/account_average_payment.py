# -*- coding: utf-8 -*-



from openerp import models, fields, api, _
from openerp import tools


class account_average_payment_report(models.Model):
    _name = "account.average.payment.report"
    _description = "Average Payment Period"
    _auto = False
    _rec_name = 'date'

    # invoice_id = fields.Many2one('account.invoice', string='Invoice', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Partner", readonly=True)
    date = fields.Date(string="Date")
    payment_date = fields.Date(string="Payment Date", readonly=True)
    payment_days = fields.Integer(string="Payment Days", readonly=True, group_operator="avg")
    period_id = fields.Many2one('account.period', string="Period", readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    move_id = fields.Many2one('account.move', string='Account Move', readonly=True)
    account_id = fields.Many2one('account.account', string="Account", readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    balance = fields.Float('Balance', readonly=True)
    pondere = fields.Float('Pondere', readonly=True)
    amount = fields.Float('Amount', readonly=True)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False,
                   lazy=True):

        new_fields = []
        new_fields += fields

        if 'payment_days' in fields:

            # new_fields.remove('payment_days')
            if 'pondere' not in new_fields:
                new_fields.append('pondere')
            if 'amount' not in new_fields:
                new_fields.append('amount')

        res = super(account_average_payment_report, self).read_group(cr, uid, domain, new_fields, groupby,
                                                                     offset=offset, limit=limit,
                                                                     context=context, orderby=orderby, lazy=lazy)

        # new_res = self.read_group(cr, uid, domain, new_fields, groupby, offset, limit, context, orderby, lazy)
        if 'payment_days' in fields:
            for line in res:
                if line['amount'] != 0.0:
                    line['payment_days'] = line['pondere'] / line['amount']
                else:
                    line['payment_days'] = 0.0
                """
                for new_line in new_res:
                    if '__domain' in line and '__domain' in new_line:
                        if line['__domain'] == new_line['__domain']:
                            if new_line['amount'] != 0.0:
                                line['payment_days'] =  new_line['pondere'] / new_line['amount']
                                break
                """
        return res

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
        select l.id,
            l.partner_id,
            l.date,
            l.payment_date,
            l.payment_days,
            l.period_id,
            l.journal_id,
            l.move_id,
            l.debit as debit,
            l.credit as credit,
            abs(coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0)) * l.payment_days as pondere,
            abs(coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0))  as amount,
            coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0) as balance


        from    account_move_line l
                left join account_move am on (am.id=l.move_id)
                left join account_journal j on (j.id = l.journal_id)
                where l.state != 'draft' and  l.reconcile_id is not null and
                      j.type in ('sale', 'purchase', 'sale_refund', 'purchase_refund')

            )""" % (
            self._table
        ))
