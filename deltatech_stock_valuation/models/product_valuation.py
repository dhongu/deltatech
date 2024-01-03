# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


# ca in SAP Material Valuation - MBEW & MBEWH
class ProductValuation(models.Model):
    _name = "product.valuation"
    _description = "Product Valuation"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product", required=True, index=True)
    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area", index=True)

    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure")
    quantity_in = fields.Float(string="Quantity In", digits="Product Unit of Measure")
    quantity_out = fields.Float(string="Quantity Out", digits="Product Unit of Measure")

    amount = fields.Monetary(string="Amount")
    debit = fields.Monetary(string="Debit")
    credit = fields.Monetary(string="Credit")

    account_id = fields.Many2one("account.account", string="Account", required=True, index=True)

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, index=True, default=lambda self: self.env.company
    )

    # _sql_constraints = [
    #     (
    #         "product_valuation_uniq",
    #         "unique (product_id, valuation_area_id, account_id, company_id)",
    #         "Product valuation must be unique",
    #     )
    # ]

    def get_valuation(self, product_id, valuation_area_id, account_id, company_id=False):
        if not company_id:
            company_id = self.env.company.id
        domain = [
            ("product_id", "=", product_id),
            ("valuation_area_id", "=", valuation_area_id),
            ("account_id", "=", account_id),
            ("company_id", "=", company_id),
        ]
        valuation = self.search(domain, limit=1)
        if not valuation:
            valuation = self.create(
                {
                    "product_id": product_id,
                    "valuation_area_id": valuation_area_id,
                    "account_id": account_id,
                    "company_id": company_id,
                }
            )
        return valuation

    def recompute_amount(self):
        for item in self:
            domain = [
                ("product_id", "=", item.product_id.id),
                ("valuation_area_id", "=", item.valuation_area_id.id),
                ("account_id", "=", item.account_id.id),
                ("company_id", "=", item.company_id.id),
            ]
            valuation = self.env["product.valuation.history"].search(domain, order="date desc", limit=1)
            if valuation:
                item.write({"quantity": valuation.quantity_final, "amount": valuation.amount_final})

    def recompute_amount_sql(self):
        valuation_areas = self.mapped("valuation_area_id")
        products = self.mapped("product_id")
        accounts = self.mapped("account_id")
        companies = self.mapped("company_id")
        domain = [
            ("product_id", "in", products.ids),
            ("account_id", "in", accounts.ids),
            ("company_id", "in", companies.ids),
        ]
        if valuation_areas:
            domain.append(("valuation_area_id", "in", valuation_areas.ids))

        params = {
            "product_ids": tuple(products.ids),
            "account_ids": tuple(accounts.ids),
            "company_ids": tuple(companies.ids),
            "valuation_area_ids": tuple(valuation_areas.ids) or (None,),
        }

        sql = """
          UPDATE product_valuation AS pv
          SET quantity = sub.quantity,
                quantity_in = sub.quantity_in,
                quantity_out = sub.quantity_out,
                debit = sub.debit,
                credit = sub.credit,
                amount = sub.debit - sub.credit
            FROM ( %s ) as sub
            WHERE
                pv.product_id = sub.product_id AND
                pv.account_id = sub.account_id AND
                pv.valuation_area_id = sub.valuation_area_id AND
                pv.company_id = sub.company_id
        """ % self._get_sql_select(
            all=False
        )

        self.env.cr.execute(sql, params)

    def _get_sql_select(self, all=True):
        sql = """
        SELECT product_id, valuation_area_id, account_id, company_id,
                sum(debit) as debit, sum(credit) as credit,
                sum(
                    quantity * (
                    CASE
                        WHEN move_type ='in_invoice' THEN 1
                        WHEN move_type ='in_refund' THEN -1
                        WHEN move_type IN ('out_invoice','out_refund') THEN 0
                        ELSE
                            CASE WHEN debit > 0 THEN 1 ELSE 0 END
                    END
                    )
                ) as quantity_in,

                sum(
                    quantity * (
                    CASE
                        WHEN move_type ='out_invoice' THEN 1
                        WHEN move_type ='out_refund' THEN -1
                        WHEN move_type IN ('in_invoice','in_refund') THEN 0
                        ELSE CASE WHEN credit > 0 THEN -1 ELSE 0 END
                    END
                    )
                ) as quantity_out,

                sum(
                    quantity * (
                    CASE WHEN move_type IN ('out_invoice','in_refund') THEN -1 ELSE 1 END
                    )
                ) as quantity

            FROM (
               %s
                ) as sub
             GROUP BY  product_id, valuation_area_id, account_id, company_id

        """ % self._get_sql_sub_select(
            all
        )
        return sql

    def _get_sql_sub_select(self, all=True):
        sql = """
                SELECT product_id, valuation_area_id, account_id, m.company_id,
                    debit, credit, move_type,
                    l.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) as quantity
                FROM account_move_line as l
                    LEFT JOIN account_move as m ON l.move_id=m.id
                    LEFT JOIN product_product product ON product.id = l.product_id
                    LEFT JOIN product_template template ON template.id = product.product_tmpl_id
                    LEFT JOIN uom_uom uom_line ON uom_line.id = l.product_uom_id
                    LEFT JOIN uom_uom uom_template ON uom_template.id = template.uom_id
                WHERE
                    account_id in %(account_ids)s
                    AND m.state = 'posted'

        """
        if not all:
            sql += """
                    AND product_id in %(product_ids)s
                    AND account_id in %(account_ids)s
                    AND valuation_area_id in %(valuation_area_ids)s
            """

        return sql

    def recompute_all_amount(self):
        params = {
            "account_ids": tuple(self.env["account.account"].search([("stock_valuation", "=", True)]).ids),
        }
        self.env.cr.execute("DELETE FROM product_valuation WHERE account_id in %(account_ids)s", params)

        sql = (
            """
            INSERT INTO product_valuation
                (product_id, valuation_area_id, account_id, company_id,
                quantity, quantity_in, quantity_out, debit, credit, amount)
            select product_id, valuation_area_id, account_id, company_id,
                         quantity, quantity_in, quantity_out, debit, credit, debit-credit as amount
            FROM ( %s ) as a
            """
            % self._get_sql_select()
        )

        self.env.cr.execute(sql, params)


class ProductValuationHistory(models.Model):
    _name = "product.valuation.history"
    _description = "Product Valuation History"
    _inherit = ["product.valuation"]
    _order = "product_id, date desc"

    year = fields.Char(string="Year", required=True, index=True)
    month = fields.Char(string="Month", required=True, index=True)
    date = fields.Date(required=True, index=True)

    amount_initial = fields.Monetary("Initial Amount", default=0.0)
    quantity_initial = fields.Float("Initial Quantity", digits="Product Unit of Measure", default=0.0)

    amount_final = fields.Monetary("Final Amount", compute="_compute_final", store=True)
    quantity_final = fields.Float(
        "Final Quantity", digits="Product Unit of Measure", compute="_compute_final", store=True
    )

    _sql_constraints = [
        (
            "product_valuation_history_uniq",
            "unique (product_id, valuation_area_id, account_id, company_id, date)",
            "Product valuation history must be unique",
        )
    ]

    def get_valuation(self, product_id, valuation_area_id, account_id, date, company_id=False):
        """
            Obtinere valoare istorica pentru un produs intr-o zona de evaluare
        :param product_id:
        :param valuation_area_id:
        :param account_id:
        :param date:
        :param company_id:
        :return:
        """
        if not company_id:
            company_id = self.env.company.id

        year = date.year
        month = date.month
        date_key = date.replace(day=1) + relativedelta(months=1, days=-1)
        domain = [
            ("product_id", "=", product_id),
            ("valuation_area_id", "=", valuation_area_id),
            ("account_id", "=", account_id),
            ("company_id", "=", company_id),
            ("date", "=", date_key),
        ]
        valuation = self.search(domain, limit=1)
        if not valuation:
            last_valuation = self.search(
                [
                    ("product_id", "=", product_id),
                    ("valuation_area_id", "=", valuation_area_id),
                    ("account_id", "=", account_id),
                    ("company_id", "=", company_id),
                    ("date", "<", date_key),
                ],
                order="date desc",
                limit=1,
            )
            if last_valuation:
                quantity_initial = last_valuation.quantity_final
                amount_initial = last_valuation.amount_final
            else:
                quantity_initial = 0
                amount_initial = 0

            valuation = self.create(
                {
                    "product_id": product_id,
                    "valuation_area_id": valuation_area_id,
                    "account_id": account_id,
                    "year": year,
                    "month": month,
                    "date": date_key,
                    "company_id": company_id,
                    "quantity_initial": quantity_initial,
                    "amount_initial": amount_initial,
                }
            )
        return valuation

    @api.depends("quantity", "amount", "quantity_initial", "amount_initial")
    def _compute_final(self):
        for s in self:
            s.quantity_final = s.quantity_initial + s.quantity
            s.amount_final = s.amount_initial + s.amount
            domain = [
                ("product_id", "=", s.product_id.id),
                ("valuation_area_id", "=", s.valuation_area_id.id),
                ("account_id", "=", s.account_id.id),
                ("company_id", "=", s.company_id.id),
                ("date", ">", s.date),
            ]
            next_valuation = self.search(domain, order="date asc", limit=1)
            if next_valuation:
                next_valuation.write(
                    {
                        "quantity_initial": s.quantity_final,
                        "amount_initial": s.amount_final,
                    }
                )

    def _get_sql_select(self, all=True):
        """
            Determinare miscari lunare insumate
        :param all:
        :return:
        """
        sql = """
                    SELECT product_id, valuation_area_id, account_id, company_id, currency_id,  year, month, date,
                sum(debit) as debit, sum(credit) as credit,
                sum(
                    quantity * (
                    CASE
                        WHEN move_type ='in_invoice' THEN 1
                        WHEN move_type ='in_refund' THEN -1
                        WHEN move_type IN ('out_invoice','out_refund') THEN 0
                        ELSE
                            CASE WHEN debit > 0 THEN 1 ELSE 0 END
                    END
                    )
                ) as quantity_in,

                sum(
                    quantity * (
                    CASE
                        WHEN move_type ='out_invoice' THEN 1
                        WHEN move_type ='out_refund' THEN -1
                        WHEN move_type IN ('in_invoice','in_refund') THEN 0
                        ELSE CASE WHEN credit > 0 THEN -1 ELSE 0 END
                    END
                    )
                ) as quantity_out,

                sum(
                    quantity * (
                    CASE WHEN move_type IN ('out_invoice','in_refund') THEN -1 ELSE 1 END
                    )
                ) as quantity

            FROM (
                 %s
                ) as sub
             GROUP BY  product_id, valuation_area_id, account_id, company_id, currency_id, year, month, date
        """ % self._get_sql_sub_select(
            all
        )
        return sql

    def _get_sql_sub_select(self, all=True):
        """
        Determinare miscari lunare
        """
        sql = """
            SELECT product_id, valuation_area_id, account_id, m.company_id, l.company_currency_id as currency_id,
                    debit, credit, move_type,
                    EXTRACT(YEAR FROM m.date) as year, EXTRACT(MONTH FROM m.date) as month,
                    (date_trunc('month', m.date) + interval '1 month - 1 day')::date as date,
                    l.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) as quantity
                FROM account_move_line as l
                    LEFT JOIN account_move as m ON l.move_id=m.id
                    LEFT JOIN product_product product ON product.id = l.product_id
                    LEFT JOIN product_template template ON template.id = product.product_tmpl_id
                    LEFT JOIN uom_uom uom_line ON uom_line.id = l.product_uom_id
                    LEFT JOIN uom_uom uom_template ON uom_template.id = template.uom_id
                WHERE
                    account_id in %(account_ids)s
                    AND m.state = 'posted'
        """
        if not all:
            sql += """
                    AND product_id in %(product_ids)s
                    AND account_id in %(account_ids)s
                    AND valuation_area_id in %(valuation_area_ids)s
                    AND EXTRACT(YEAR FROM m.date)  in %(year)s
                    AND EXTRACT(MONTH FROM m.date) in %(month)s
            """

        return sql

    def recompute_amount(self):
        valuation_areas = self.mapped("valuation_area_id")
        products = self.mapped("product_id")
        accounts = self.mapped("account_id")
        companies = self.mapped("company_id")

        params = {
            "product_ids": tuple(products.ids),
            "account_ids": tuple(accounts.ids),
            "year": tuple(self.mapped("year")),
            "month": tuple(self.mapped("month")),
            "date": tuple(self.mapped("date")),
            "company_ids": tuple(companies.ids),
            "valuation_area_ids": tuple(valuation_areas.ids) or (None,),
        }
        sql = """


           UPDATE product_valuation_history AS pv
            SET quantity = sub.quantity,
                quantity_in = sub.quantity_in,
                quantity_out = sub.quantity_out,
                debit = sub.debit,
                credit = sub.credit,
                amount = sub.debit - sub.credit
            FROM ( %s ) as sub
            WHERE
                pv.product_id = sub.product_id AND
                pv.account_id = sub.account_id AND
                pv.valuation_area_id = sub.valuation_area_id AND
                pv.company_id = sub.company_id AND

                pv.date = sub.date
        """ % self._get_sql_select(
            all=False
        )
        self.env.cr.execute(sql, params)
        # invalidate chashed fields
        self.invalidate_cache()
        self._compute_final()

    def recompute_all_amount(self):
        """
         Recalculare istoric valorilor
        :return:
        """

        self.env.company.set_stock_valuation_at_company_level()

        valuation_area = self.env.company.valuation_area_id

        params = {
            "account_ids": tuple(self.env["account.account"].search([("stock_valuation", "=", True)]).ids),
            "valuation_area_id": valuation_area.id,
            "company_id": self.env.company.id,
            "currency_id": self.env.company.currency_id.id,
        }

        _logger.info("Stergere linii istoric")
        self.env.cr.execute(
            """
            DELETE FROM product_valuation_history WHERE valuation_area_id = %(valuation_area_id)s;
        """,
            params,
        )
        _logger.info("Calculare linii istoric miscari lunare")

        sql = (
            """
            INSERT INTO product_valuation_history
                (product_id, valuation_area_id, account_id, company_id, currency_id, year, month, date,
                quantity, quantity_in, quantity_out, debit, credit, amount)
            SELECT product_id, valuation_area_id, account_id, company_id, currency_id, year, month, date,
                        quantity, quantity_in, quantity_out, debit, credit, debit-credit as amount
            FROM ( %s ) as a
        """
            % self._get_sql_select()
        )

        self.env.cr.execute(sql, params)

        _logger.info("resetare Sold initial si final")
        self.env.cr.execute(
            """
            UPDATE product_valuation_history AS pv
                SET
                    quantity_initial = 0,
                    quantity_final = pv.quantity,
                    amount_initial = 0,
                    amount_final = pv.amount
        """
        )

        # optinere data minima si maxima
        self.env.cr.execute(
            """
            SELECT min(date) as min_date, max(date) as max_date
            FROM product_valuation_history
            WHERE valuation_area_id = %(valuation_area_id)s
            """,
            params,
        )
        res = self.env.cr.dictfetchone()

        params["min_date"] = res["min_date"]
        params["max_date"] = res["max_date"]

        _logger.info("Adaugare linii lipsa")
        self.env.cr.execute(
            """
            DROP TABLE IF EXISTS calendar_temporal;
            CREATE TEMP TABLE calendar_temporal AS
            SELECT
                (date_trunc('MONTH', generate_series) + INTERVAL '1 MONTH' - INTERVAL '1 day')::DATE AS date
            FROM
                generate_series(%(min_date)s::date, %(max_date)s::date, '1 month'::interval) ;

            INSERT INTO product_valuation_history
            (
                product_id, valuation_area_id, account_id, company_id, currency_id, date, year, month,
                quantity, amount, quantity_initial, amount_initial, quantity_final, amount_final
            )
            SELECT
                p.product_id,
                %(valuation_area_id)s as valuation_area_id,
                a.account_id,
                %(company_id)s as company_id,
                %(currency_id)s as currency_id,
                c.date,
                date_part('year', c.date) AS year,
                date_part('month', c.date) AS month,
                0 as quantity,
                0 as amount,
                0 as quantity_initial,
                0 as amount_initial,
                0 as quantity_final,
                0 as amount_final

            FROM
                calendar_temporal c
            CROSS JOIN (SELECT DISTINCT product_id FROM product_valuation_history) p
            CROSS JOIN (SELECT DISTINCT account_id FROM product_valuation_history) a

            WHERE NOT EXISTS (
                SELECT 1
                FROM product_valuation_history pv
                WHERE
                    pv.product_id = p.product_id AND
                    pv.valuation_area_id =  %(valuation_area_id)s AND
                    pv.account_id = a.account_id AND
                    pv.company_id = %(company_id)s AND
                    pv.date = c.date
            )

            """,
            params,
        )

        _logger.info("Calculare sold initial si final")
        self.env.cr.execute(
            """
                UPDATE product_valuation_history AS pv
                SET
                    quantity_initial = cv.quantity_initial,
                    amount_initial = cv.amount_initial,
                    quantity_final = cv.quantity_final,
                    amount_final =  cv.amount_final
                FROM (
                    SELECT
                        product_id,
                        valuation_area_id,
                        account_id,
                        company_id,
                        date,
                        COALESCE(LAG(quantity_final) OVER (
                            PARTITION BY product_id, valuation_area_id, account_id, company_id
                             ORDER BY date), 0) AS quantity_initial,
                        COALESCE(LAG(amount_final) OVER (
                            PARTITION BY product_id, valuation_area_id, account_id, company_id
                            ORDER BY date), 0)  AS amount_initial,
                        SUM(quantity) OVER (
                            PARTITION BY product_id, valuation_area_id, account_id, company_id
                             ORDER BY date) AS quantity_final,
                        SUM(amount) OVER (
                            PARTITION BY product_id, valuation_area_id, account_id, company_id
                            ORDER BY date) AS amount_final
                    FROM
                        product_valuation_history
                ) AS cv
                WHERE
                    pv.product_id = cv.product_id AND
                    pv.account_id = cv.account_id AND
                    pv.valuation_area_id = cv.valuation_area_id AND
                    pv.valuation_area_id = %(valuation_area_id)s AND
                    pv.company_id = cv.company_id AND
                    pv.company_id = %(company_id)s AND
                    pv.date = cv.date;

            """,
            params,
        )

        _logger.info("Calculare sold initial ")
        self.env.cr.execute(
            """
            UPDATE product_valuation_history
                SET
                    quantity_initial =  quantity_final - quantity,
                    amount_initial = amount_final - amount
            WHERE  valuation_area_id = %(valuation_area_id)s ;

            """,
            params,
        )
        _logger.info("Sterge linii goale ")
        self.env.cr.execute(
            """
            DELETE FROM product_valuation_history
            WHERE  valuation_area_id = %(valuation_area_id)s
                and (quantity_initial is null or quantity_initial = 0)
                and (quantity_final is null or quantity_final = 0)
                and (quantity is null or quantity = 0)
                and (amount_initial is null or amount_initial = 0)
                and (amount is null or amount = 0)
                and (amount_final is null or amount_final = 0)

            """,
            params,
        )

        _logger.info("FINALIZARE CALCULARE ISTORIC VALORI")
