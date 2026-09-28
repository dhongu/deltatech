# ©  2026 Terrabit
# Based on the MD Trade customer analysis modules, © 2026 MD Trade Concept SRL
# See README.rst file on addons root folder for license details
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

RHYTHM_SEGMENTS = [
    ("new", "New"),
    ("active", "Active"),
    ("at_risk", "At risk"),
    ("dormant", "Dormant"),
    ("lost", "Lost"),
]

CLASSIFICATIONS = [
    ("top_client", "Top customer"),
    ("growing", "Growing"),
    ("high_potential", "High potential"),
    ("small_orders", "Small orders (upsell)"),
    ("stable", "Stable"),
    ("declining", "Declining"),
    ("inactive_1", "Inactive, level 1"),
    ("inactive_2", "Inactive, level 2"),
    ("inactive_3", "Inactive, level 3"),
    ("overdue_risk", "Payment risk"),
]

# Columns written by the engine, in the order of the INSERT below
ENGINE_COLUMNS = [
    "partner_id",
    "company_id",
    "basis",
    "first_date",
    "last_date",
    "days_since",
    "interval_days",
    "sale_count",
    "sale_count_12m",
    "revenue_total",
    "revenue_12m",
    "revenue_current",
    "revenue_previous",
    "growth_pct",
    "avg_amount",
    "open_balance",
    "overdue_amount",
    "overdue_invoice_count",
    "max_overdue_days",
    "last_contact_date",
    "is_top_client",
    "is_high_value",
    "rhythm_segment",
    "classification",
    "risk_score",
    "potential_score",
    "computed_on",
]


class CustomerSegment(models.Model):
    """One row per customer (commercial partner) and company.

    Written only by the nightly engine, in SQL: these are aggregates over the
    whole sales history, a stored compute on res.partner would be re-evaluated
    on every partner write. A customer without any sale in the company has no
    row (a prospect).
    """

    _name = "deltatech.customer.segment"
    _description = "Customer Segment"
    _order = "revenue_12m desc, id"
    _rec_name = "partner_id"
    _check_company_auto = True

    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, readonly=True, index=True, ondelete="cascade"
    )
    company_id = fields.Many2one("res.company", required=True, readonly=True, index=True, ondelete="cascade")
    currency_id = fields.Many2one(related="company_id.currency_id")
    user_id = fields.Many2one(related="partner_id.user_id", string="Salesperson")
    category_ids = fields.Many2many(related="partner_id.category_id", string="Tags")
    basis = fields.Selection(
        [("invoices", "Invoices"), ("orders", "Orders")], readonly=True, help="Documents the row was computed from."
    )

    first_date = fields.Date(string="First purchase", readonly=True)
    last_date = fields.Date(string="Last purchase", readonly=True)
    days_since = fields.Integer(string="Days since last purchase", readonly=True, aggregator="avg")
    interval_days = fields.Integer(
        string="Rhythm (days)",
        readonly=True,
        aggregator="avg",
        help="Average number of days between purchases, measured. Empty for a single purchase.",
    )
    sale_count = fields.Integer(string="Purchases", readonly=True)
    sale_count_12m = fields.Integer(string="Purchases (12 months)", readonly=True)

    revenue_total = fields.Monetary(string="Lifetime sales", readonly=True)
    revenue_12m = fields.Monetary(string="Sales (12 months)", readonly=True)
    revenue_current = fields.Monetary(string="Sales (current period)", readonly=True)
    revenue_previous = fields.Monetary(string="Sales (previous period)", readonly=True)
    growth_pct = fields.Float(string="Growth (%)", readonly=True, digits=(16, 1), aggregator="avg")
    avg_amount = fields.Monetary(string="Average purchase", readonly=True, aggregator="avg")

    open_balance = fields.Monetary(readonly=True)
    overdue_amount = fields.Monetary(readonly=True)
    overdue_invoice_count = fields.Integer(string="Overdue invoices", readonly=True)
    max_overdue_days = fields.Integer(string="Oldest overdue (days)", readonly=True, aggregator="max")
    last_contact_date = fields.Datetime(string="Last contact", readonly=True)

    is_top_client = fields.Boolean(string="Top customer", readonly=True)
    is_high_value = fields.Boolean(string="High value", readonly=True)
    rhythm_segment = fields.Selection(
        RHYTHM_SEGMENTS,
        string="Rhythm",
        readonly=True,
        index=True,
        help="Where the customer stands against his own buying rhythm, not against a company average.",
    )
    classification = fields.Selection(CLASSIFICATIONS, readonly=True, index=True)
    risk_score = fields.Integer(readonly=True, aggregator="avg")
    potential_score = fields.Integer(readonly=True, aggregator="avg")
    computed_on = fields.Datetime(readonly=True)

    _partner_company_uniq = models.Constraint(
        "unique(partner_id, company_id)", "A customer has a single segment row per company."
    )

    # ------------------------------------------------------------------
    # Engine
    # ------------------------------------------------------------------
    @api.model
    def _cron_recompute(self):
        """Recompute every company; a failing company does not stop the others."""
        companies = self.env["res.company"].search([("active", "=", True)])
        for company in companies:
            try:
                with self.env.cr.savepoint():
                    self._recompute_company(company)
            except Exception:
                _logger.exception("Customer segment recompute failed for company %s", company.display_name)

    @api.model
    def _recompute_company(self, company):
        """Recompute all the rows of a company in a single statement."""
        config = self.env["deltatech.customer.segment.config"]._get_for_company(company)
        # Raw SQL does not see the records still pending in the ORM cache
        self.env.flush_all()
        now = fields.Datetime.now()
        query = self._get_engine_query(config, now)
        self.env.cr.execute(query)
        partner_ids = [row[0] for row in self.env.cr.fetchall()]
        touched = len(partner_ids)
        # Customers without sales any more (cancelled documents, excluded by the settings)
        self.env.cr.execute(
            SQL(
                "DELETE FROM deltatech_customer_segment WHERE company_id = %s AND NOT (partner_id = ANY(%s))",
                company.id,
                partner_ids,
            )
        )
        config.sudo().last_run = now
        self.env.invalidate_all()
        _logger.info("Customer segments: %s rows for company %s", touched, company.display_name)
        return touched

    @api.model
    def _get_period_dates(self, config, today):
        months = config.period_months
        current_from = today - relativedelta(months=months) + relativedelta(days=1)
        previous_to = current_from - relativedelta(days=1)
        previous_from = previous_to - relativedelta(months=months) + relativedelta(days=1)
        return current_from, previous_from, previous_to

    @api.model
    def _get_documents_query(self, config):
        """One row per sale document: partner, date, untaxed amount in company currency.

        Invoices: amount_untaxed_signed is already in company currency and
        negative on credit notes. Orders: the order rate is company -> order
        currency, so the amount is divided by it.
        """
        company_id = config.company_id.id
        if config.basis == "orders":
            return SQL(
                """
                SELECT COALESCE(rp.commercial_partner_id, rp.id) AS pid,
                       so.date_order::date AS doc_date,
                       so.amount_untaxed / COALESCE(NULLIF(so.currency_rate, 0), 1.0) AS amount,
                       TRUE AS is_sale
                  FROM sale_order so
                  JOIN res_partner rp ON rp.id = so.partner_id
                 WHERE so.state = 'sale'
                   AND so.company_id = %(company_id)s
                """,
                company_id=company_id,
            )
        return SQL(
            """
            SELECT m.commercial_partner_id AS pid,
                   m.invoice_date AS doc_date,
                   m.amount_untaxed_signed AS amount,
                   m.move_type = 'out_invoice' AS is_sale
              FROM account_move m
             WHERE m.state = 'posted'
               AND m.move_type IN ('out_invoice', 'out_refund')
               AND m.company_id = %(company_id)s
               AND m.invoice_date IS NOT NULL
               AND m.commercial_partner_id IS NOT NULL
            """,
            company_id=company_id,
        )

    @api.model
    def _get_engine_query(self, config, now):
        today = fields.Date.context_today(self)
        current_from, previous_from, previous_to = self._get_period_dates(config, today)
        month_from = today.replace(day=1)
        prev_month_to = month_from - relativedelta(days=1)
        prev_month_from = prev_month_to.replace(day=1)
        partner_filter = SQL("AND cp.is_company") if config.only_companies else SQL()
        insert_columns = SQL(", ").join(SQL.identifier(col) for col in ENGINE_COLUMNS)
        update_columns = SQL(", ").join(
            SQL("%s = EXCLUDED.%s", SQL.identifier(col), SQL.identifier(col))
            for col in ENGINE_COLUMNS
            if col not in ("partner_id", "company_id")
        )
        return SQL(
            """
            WITH docs AS (%(docs)s),
            agg AS (
                SELECT pid,
                       MIN(doc_date) FILTER (WHERE is_sale) AS first_date,
                       MAX(doc_date) FILTER (WHERE is_sale) AS last_date,
                       COUNT(*) FILTER (WHERE is_sale) AS sale_count,
                       COUNT(*) FILTER (WHERE is_sale AND doc_date > %(year_ago)s) AS sale_count_12m,
                       SUM(amount) AS revenue_total,
                       COALESCE(SUM(amount) FILTER (WHERE doc_date > %(year_ago)s), 0) AS revenue_12m,
                       COALESCE(SUM(amount) FILTER (WHERE doc_date >= %(cur_from)s), 0) AS revenue_current,
                       COALESCE(SUM(amount) FILTER (
                           WHERE doc_date BETWEEN %(prev_from)s AND %(prev_to)s), 0) AS revenue_previous,
                       COALESCE(SUM(amount) FILTER (WHERE doc_date >= %(month_from)s), 0) AS revenue_month,
                       COALESCE(SUM(amount) FILTER (
                           WHERE doc_date BETWEEN %(prev_month_from)s AND %(prev_month_to)s), 0) AS revenue_prev_month
                  FROM docs
                 WHERE doc_date <= %(today)s
                 GROUP BY pid
                HAVING COUNT(*) FILTER (WHERE is_sale) > 0
            ),
            bal AS (
                SELECT m.commercial_partner_id AS pid,
                       SUM(m.amount_residual_signed) AS open_balance,
                       COALESCE(SUM(m.amount_residual_signed) FILTER (
                           WHERE COALESCE(m.invoice_date_due, m.invoice_date) < %(today)s), 0) AS overdue_amount,
                       COUNT(*) FILTER (
                           WHERE m.move_type = 'out_invoice'
                             AND m.amount_residual_signed > %(tolerance)s
                             AND COALESCE(m.invoice_date_due, m.invoice_date) < %(today)s) AS overdue_invoice_count,
                       MAX(%(today)s - COALESCE(m.invoice_date_due, m.invoice_date)) FILTER (
                           WHERE m.amount_residual_signed > %(tolerance)s
                             AND COALESCE(m.invoice_date_due, m.invoice_date) < %(today)s) AS max_overdue_days
                  FROM account_move m
                 WHERE m.state = 'posted'
                   AND m.move_type IN ('out_invoice', 'out_refund')
                   AND m.payment_state IN ('not_paid', 'partial')
                   AND m.company_id = %(company_id)s
                 GROUP BY m.commercial_partner_id
            ),
            contact AS (
                -- Messages logged on the company or on any of its contacts
                SELECT rp.commercial_partner_id AS pid, MAX(mm.date) AS last_contact
                  FROM mail_message mm
                  JOIN res_partner rp ON rp.id = mm.res_id
                 WHERE mm.model = 'res.partner'
                   AND mm.message_type IN ('comment', 'email', 'email_outgoing')
                   AND rp.commercial_partner_id IN (SELECT pid FROM agg)
                 GROUP BY rp.commercial_partner_id
            ),
            calc AS (
                SELECT agg.*,
                       %(today)s - agg.last_date AS days_since,
                       CASE WHEN agg.sale_count > 1
                            THEN GREATEST(ROUND((agg.last_date - agg.first_date)::numeric
                                                / (agg.sale_count - 1))::int, 1)
                       END AS interval_days,
                       agg.revenue_total / agg.sale_count AS avg_amount,
                       CASE WHEN agg.revenue_previous > 0
                            THEN (agg.revenue_current - agg.revenue_previous) / agg.revenue_previous * 100
                            WHEN agg.revenue_current > 0 THEN 100
                            ELSE 0
                       END AS growth_pct,
                       COALESCE(bal.open_balance, 0) AS open_balance,
                       COALESCE(bal.overdue_amount, 0) AS overdue_amount,
                       COALESCE(bal.overdue_invoice_count, 0) AS overdue_invoice_count,
                       COALESCE(bal.max_overdue_days, 0) AS max_overdue_days,
                       contact.last_contact,
                       agg.revenue_total >= %(high_value_min)s AS is_high_value,
                       (contact.last_contact IS NULL
                        OR %(today)s - contact.last_contact::date >= %(neglected_days)s) AS no_recent_contact
                  FROM agg
                  JOIN res_partner cp ON cp.id = agg.pid
                  LEFT JOIN bal ON bal.pid = agg.pid
                  LEFT JOIN contact ON contact.pid = agg.pid
                 WHERE TRUE %(partner_filter)s
            ),
            ranked AS (
                SELECT calc.*,
                       ROW_NUMBER() OVER (ORDER BY revenue_total DESC, pid) AS rn,
                       COUNT(*) FILTER (WHERE revenue_total > 0) OVER () AS positive_count
                  FROM calc
            ),
            classified AS (
                SELECT ranked.*,
                       revenue_total > 0
                       AND rn <= LEAST(GREATEST(%(top_min)s, CEIL(positive_count * %(top_share)s / 100.0)),
                                         positive_count) AS is_top_client,
                       CASE
                           WHEN days_since > %(lost_after)s THEN 'lost'
                           -- A new relationship is judged by its age: one purchase has no rhythm yet
                           WHEN first_date >= %(new_from)s AND sale_count <= %(new_max)s THEN 'new'
                           WHEN days_since <= COALESCE(interval_days, %(default_interval)s) * %(at_risk_factor)s
                               THEN 'active'
                           WHEN days_since <= COALESCE(interval_days, %(default_interval)s) * %(dormant_factor)s
                               THEN 'at_risk'
                           ELSE 'dormant'
                       END AS rhythm_segment,
                       CASE
                           WHEN days_since >= %(inactive_3)s THEN 'inactive_3'
                           WHEN days_since >= %(inactive_2)s THEN 'inactive_2'
                           WHEN days_since >= %(inactive_1)s THEN 'inactive_1'
                           WHEN open_balance > %(tolerance)s
                                AND (max_overdue_days >= %(overdue_days)s
                                     OR overdue_invoice_count >= %(overdue_count)s) THEN 'overdue_risk'
                           WHEN revenue_previous >= %(decline_min_previous)s
                                AND revenue_current < revenue_previous * %(decline_ratio)s THEN 'declining'
                           WHEN revenue_previous > 0
                                AND revenue_current > revenue_previous * %(growth_ratio)s THEN 'growing'
                           WHEN revenue_total >= %(high_potential_min)s
                                AND avg_amount >= %(high_potential_avg)s THEN 'high_potential'
                           WHEN sale_count >= 3 AND avg_amount > 0 AND avg_amount < %(small_order_avg)s
                               THEN 'small_orders'
                           ELSE 'stable'
                       END AS base_classification,
                       -- Scores kept from the MD Trade formulas
                       ROUND(
                           GREATEST(open_balance, 0) * 0.002
                           + max_overdue_days * 1.35
                           + days_since * 0.95
                           + GREATEST(-growth_pct, 0)
                           + CASE WHEN no_recent_contact THEN 35 ELSE 0 END
                           + CASE WHEN is_high_value THEN 40 ELSE 0 END
                           + CASE WHEN overdue_invoice_count >= 3 THEN 24 ELSE 0 END
                       )::int AS risk_score,
                       ROUND(
                           GREATEST(LEAST(growth_pct, 1000), 0)
                           + CASE WHEN revenue_prev_month > 0 AND revenue_month > revenue_prev_month THEN 20 ELSE 0 END
                           + CASE WHEN sale_count >= 3 AND avg_amount > 0
                                       AND avg_amount < %(high_potential_avg)s THEN 18 ELSE 0 END
                           + CASE WHEN is_high_value THEN 15 ELSE 0 END
                           - CASE WHEN days_since > %(inactive_2)s THEN 25 ELSE 0 END
                       )::int AS potential_score
                  FROM ranked
            )
            INSERT INTO deltatech_customer_segment (%(insert_columns)s,
                                                    create_uid, create_date, write_uid, write_date)
            SELECT pid, %(company_id)s, %(basis)s, first_date, last_date, days_since, interval_days,
                   sale_count, sale_count_12m,
                   ROUND(revenue_total, 2), ROUND(revenue_12m, 2),
                   ROUND(revenue_current, 2), ROUND(revenue_previous, 2),
                   ROUND(growth_pct, 1), ROUND(avg_amount, 2),
                   ROUND(open_balance, 2), ROUND(overdue_amount, 2),
                   overdue_invoice_count, max_overdue_days, last_contact,
                   is_top_client, is_high_value, rhythm_segment,
                   CASE WHEN is_top_client
                             AND base_classification IN ('stable', 'growing', 'high_potential', 'small_orders')
                        THEN 'top_client'
                        ELSE base_classification
                   END,
                   risk_score, potential_score, %(now)s,
                   %(uid)s, %(now)s, %(uid)s, %(now)s
              FROM classified
            ON CONFLICT (partner_id, company_id) DO UPDATE SET %(update_columns)s,
                   write_uid = EXCLUDED.write_uid, write_date = EXCLUDED.write_date
            RETURNING partner_id
            """,
            docs=self._get_documents_query(config),
            company_id=config.company_id.id,
            basis=config.basis,
            today=today,
            now=now,
            uid=self.env.uid,
            year_ago=today - relativedelta(years=1),
            cur_from=current_from,
            prev_from=previous_from,
            prev_to=previous_to,
            month_from=month_from,
            prev_month_from=prev_month_from,
            prev_month_to=prev_month_to,
            new_from=today - relativedelta(days=config.new_days),
            new_max=config.new_max_count,
            lost_after=config.lost_after_days,
            default_interval=config.default_interval_days or 1,
            at_risk_factor=config.at_risk_factor,
            dormant_factor=config.dormant_factor,
            inactive_1=config.inactive_days_1,
            inactive_2=config.inactive_days_2,
            inactive_3=config.inactive_days_3,
            tolerance=config.overdue_tolerance,
            overdue_days=config.overdue_days,
            overdue_count=config.overdue_count,
            decline_min_previous=config.decline_min_previous,
            decline_ratio=config.decline_pct / 100.0,
            growth_ratio=1 + config.growth_pct / 100.0,
            high_value_min=config.high_value_min,
            high_potential_min=config.high_potential_min,
            high_potential_avg=config.high_potential_avg,
            small_order_avg=config.small_order_avg,
            top_share=config.top_share_pct,
            top_min=config.top_min_count,
            neglected_days=config.neglected_contact_days,
            partner_filter=partner_filter,
            insert_columns=insert_columns,
            update_columns=update_columns,
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    @api.model
    def action_open_for_partners(self, partner_ids):
        """Opened from the partner form (bound server action)."""
        partners = self.env["res.partner"].browse(partner_ids).commercial_partner_id
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Customer Segment"),
            "res_model": self._name,
            "view_mode": "list,form",
            "domain": [("partner_id", "in", partners.ids)],
        }
