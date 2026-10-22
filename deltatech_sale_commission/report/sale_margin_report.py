# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.exceptions import AccessError

# the columns of the commission rates, from the lateral join "cu"
RATE_COLUMNS = ("rate", "manager_rate", "director_rate", "manager_user_id", "director_user_id")


class SaleMarginReport(models.Model):
    _inherit = "sale.margin.report"

    commission_computed = fields.Float("Commission Computed", readonly=True)
    commission_manager_computed = fields.Float("Commission Manager Computed", readonly=True)
    commission_director_computed = fields.Float("Commission Director Computed", readonly=True)

    commission = fields.Float("Real Commission")
    commission_paid = fields.Boolean("Commission Paid", default=False)

    manager_user_id = fields.Many2one("res.users", "Sales Manager", readonly=True)
    director_user_id = fields.Many2one("res.users", "Sales Director", readonly=True)

    def _select(self):
        return (
            super()._select()
            + """
                , sub.rate * (sale_val  - stock_val ) as commission_computed,
                sub.manager_rate * (sale_val    - stock_val )  as commission_manager_computed,
                sub.director_rate * (sale_val    - stock_val )  as commission_director_computed,
                commission,
                commission_paid,
                manager_user_id, director_user_id
        """
        )

    def _sub_select(self):
        return (
            super()._sub_select()
            + """
                    , sum(l.commission) as commission,
                    bool_and(l.commission_paid) as commission_paid,
                    cu.rate, cu.manager_rate, cu.director_rate, cu.manager_user_id, cu.director_user_id
        """
        )

    def _user_column(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if get_param("sale_commission.sale_user_detail", "invoice") == "invoice":
            return super()._user_column()
        return "l.sale_user_id"

    def _from(self):
        # At most one rate row per invoice line, whatever the data: a plain join multiplies the
        # line by every matching row, so a duplicate rate doubles the sale, cost and profit
        # (same rates, same report line) or the line itself (different rates, repeated id).
        # The unique constraint on commission.users is not enough on its own: it can not be
        # created while old duplicates are still there.
        #
        # "order by c.id limit 1" takes the *oldest* of the duplicates, the same row the migration
        # keeps when it deletes the exact duplicates. For duplicates whose rates differ the choice
        # is arbitrary and probably wrong either way — the newest row is as likely to be the
        # current rate as the oldest is — so it is deliberately not a decision taken here: the
        # migration and the precheck script both report those rows so that someone picks one. This
        # LIMIT is only there to keep the report honest (one line, one rate) while they are left.
        #
        # c.company_id = s.company_id is new in 19.0.1.6.0. The old join matched on salesperson and
        # journal only, so a row filed under the wrong company still applied. It no longer does,
        # which is right — but on an existing database it silently takes a commission away, hence
        # the check in scripts/sale_commission_precheck_1_6_0.py and the ORM constraint on the model.
        return super()._from() + self._commission_rate_join(self._user_column(), "s.journal_id", "s.company_id")

    def _group_by(self):
        return super()._group_by() + ", " + ", ".join(f"cu.{column}" for column in RATE_COLUMNS)

    @staticmethod
    def _commission_rate_join(user_column, journal_column, company_column):
        """The rates of the salesperson on the journal, as the lateral join ``cu`` (one row at most)."""
        return f"""
                    left join lateral (
                        select c.rate, c.manager_rate, c.director_rate, c.manager_user_id, c.director_user_id
                          from commission_users c
                         where c.user_id = {user_column}
                           and c.journal_id = {journal_column}
                           and c.company_id = {company_column}
                      order by c.id
                         limit 1
                    ) cu on true
        """

    def _prepare_extra_source(self, source):
        # the other sources get the rates of their salesperson on their journal, so the computed
        # commission is there for them too; the real commission stays on the invoice lines
        source = super()._prepare_extra_source(source)
        rate_join = self._commission_rate_join(
            source["user_column"], source["journal_column"], source["company_column"]
        )
        rate_columns = {column: f"cu.{column}" for column in RATE_COLUMNS}
        return dict(source, **{"from": source["from"] + rate_join, "columns": dict(source["columns"], **rate_columns)})

    def _invoice_line_fields(self):
        return super()._invoice_line_fields() + ["commission", "commission_paid"]

    def write(self, vals):
        # The sales managers may write the report (the cost, from deltatech_sale_margin), but the
        # commission itself stays with the commission managers, as before the split.
        if {"commission", "commission_paid"} & set(vals) and not self.env.user.has_group(
            "deltatech_sale_commission.group_commission_manager"
        ):
            raise AccessError(self.env._("Only a Commission Manager can change the commission."))
        return super().write(vals)

    def action_set_commission_paid(self):
        # the rows of the other sources have no commission to mark, they are left out
        for record in self._invoice_rows():
            record.write({"commission_paid": True})
