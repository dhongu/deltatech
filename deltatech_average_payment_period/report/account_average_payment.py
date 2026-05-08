# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, tools


class AccountAveragePaymentReport(models.Model):
    _name = "account.average.payment.report"
    _description = "Average Payment Period"
    _auto = False
    _rec_name = "date"

    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    date = fields.Date(string="Date")
    payment_date = fields.Date(string="Payment Date", readonly=True)
    payment_days = fields.Integer(string="Payment Days", readonly=True, aggregator="avg")
    # period_id = fields.Many2one('account.period', string="Period", readonly=True)
    journal_id = fields.Many2one("account.journal", string="Journal", readonly=True)
    move_id = fields.Many2one("account.move", string="Account Move", readonly=True)
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

    @api.model
    def _read_group(
        self,
        domain: list,
        groupby: list[str] = (),
        aggregates: list[str] = (),
        having: list = (),
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[tuple]:
        new_aggregates = list(aggregates)

        # Check if 'payment_days' is in aggregates (either as 'payment_days' or 'payment_days:avg')
        payment_days_agg = [agg for agg in aggregates if agg.split(":")[0] == "payment_days"]

        if payment_days_agg:
            if "weight:sum" not in new_aggregates:
                new_aggregates.append("weight:sum")
            if "amount:sum" not in new_aggregates:
                new_aggregates.append("amount:sum")

        res = super()._read_group(domain, groupby, new_aggregates, having, offset, limit, order)

        if payment_days_agg:
            # res is a list of tuples: (group_values..., aggregate_values...)
            # We need to find the indices of payment_days, weight, and amount in the result tuples.

            # Result tuple structure: groupby values followed by aggregate values
            offset_agg = len(groupby)
            try:
                pd_idx = offset_agg + aggregates.index(payment_days_agg[0])
                weight_idx = offset_agg + new_aggregates.index("weight:sum")
                amount_idx = offset_agg + new_aggregates.index("amount:sum")

                new_res = []
                for row in res:
                    row_list = list(row)
                    weight = row_list[weight_idx] or 0.0
                    amount = row_list[amount_idx] or 0.0
                    if amount != 0.0:
                        payment_days = weight / amount
                    else:
                        payment_days = 0.0
                    row_list[pd_idx] = abs(payment_days)
                    # Omit the extra aggregates we added if they weren't requested
                    new_res.append(tuple(row_list[: offset_agg + len(aggregates)]))
                return new_res
            except (ValueError, IndexError):
                return res

        return res

    def _select(self):
        sql = """
         select l.id,
            l.partner_id,
            l.date,
            l.payment_date,
            l.payment_days,

            l.journal_id,
            l.move_id,
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
            f"""CREATE or REPLACE VIEW {self._table} as (
                {self._select()}
                {self._from()}
            )"""
        )
