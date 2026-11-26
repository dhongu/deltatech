# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models, tools
from odoo.tools import SQL


class AccountAveragePaymentReport(models.Model):
    _name = "account.average.payment.report"
    _description = "Average Payment Period"
    _auto = False
    _rec_name = "date"

    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    date = fields.Date(string="Date")
    payment_date = fields.Date(string="Payment Date", readonly=True)
    payment_days = fields.Float(string="Payment Days", readonly=True, aggregator="avg")
    # period_id = fields.Many2one('account.period', string="Period", readonly=True)
    journal_id = fields.Many2one("account.journal", string="Journal", readonly=True)
    move_id = fields.Many2one("account.move", string="Account Move", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    ref = fields.Char("Reference", readonly=True)
    # invoice_id = fields.Many2one('account.invoice',string="Invoice",readonly=True)
    account_code = fields.Char(string="Account Code", related="account_id.code", readonly=True)
    account_id = fields.Many2one("account.account", string="Account", readonly=True)
    debit = fields.Float("Debit", readonly=True)
    credit = fields.Float("Credit", readonly=True)
    balance = fields.Float("Balance", readonly=True)
    weight = fields.Float("Weight", readonly=True)
    amount = fields.Float("Amount", readonly=True)
    payment_days_simple = fields.Float("Plain payment days", readonly=True, aggregator="avg")

    def _read_group_select(self, aggregate_spec, query):
        # Media zilelor de plată, ponderată cu valoarea: sum(valoare × zile) / sum(valoare).
        # Se aplică la nivel SQL, ca să fie aceeași în pivot (_read_grouping_sets), grafic și
        # listă (_read_group); o medie aritmetică ar supraevalua facturile mici plătite târziu.
        if aggregate_spec == "payment_days:avg":
            weight = self._field_to_sql(self._table, "weight", query)
            amount = self._field_to_sql(self._table, "amount", query)
            return SQL("COALESCE(ABS(SUM(%s) / NULLIF(SUM(%s), 0)), 0)", weight, amount)
        return super()._read_group_select(aggregate_spec, query)

    def _select(self):
        sql = """
         select l.id,
            l.partner_id,
            l.date,
            l.payment_date,
            l.payment_days,

            l.journal_id,
            l.move_id,
            l.company_id,
            l.debit as debit,
            l.credit as credit,
            am.ref as ref,
            l.account_id as account_id,

            abs(coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0)) * l.payment_days as weight,
            abs(coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0))  as amount,
            coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0) as balance,
            l.payment_days_simple as payment_days_simple

        """
        return sql

    def _from(self):
        sql = """
                from    account_move_line l
                left join account_move am on (am.id=l.move_id)
                left join account_journal j on (j.id = l.journal_id)
                left join account_account a on (a.id = l.account_id)
                where am.state = 'posted' and  l.full_reconcile_id is not null and
                      j.type in ('sale', 'purchase', 'sale_refund', 'purchase_refund')

        """
        return sql

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            SQL(
                "CREATE or REPLACE VIEW %s as (%s %s)",
                SQL.identifier(self._table),
                SQL(self._select()),
                SQL(self._from()),
            )
        )
