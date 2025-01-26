# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


# ca in SAP Material Valuation - MBEW & MBEWH
class ProductValuation(models.Model):
    _name = "product.valuation"
    _description = "Product Valuation"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product", required=True, index=True)
    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area", index=True)

    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure", default=0.0)
    quantity_in = fields.Float(string="Quantity In", digits="Product Unit of Measure", default=0.0)
    quantity_out = fields.Float(string="Quantity Out", digits="Product Unit of Measure", default=0.0)

    amount = fields.Monetary(string="Amount", default=0.0)
    debit = fields.Monetary(string="Debit", default=0.0)
    credit = fields.Monetary(string="Credit", default=0.0)

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
            valuation = self.env["product.valuation.history"].search(domain, order="month desc", limit=1)
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

        sql = f"""
          UPDATE product_valuation AS pv
          SET quantity = sub.quantity,
                quantity_in = sub.quantity_in,
                quantity_out = sub.quantity_out,
                debit = sub.debit,
                credit = sub.credit,
                amount = sub.debit - sub.credit
            FROM ( {self._get_sql_select(all_records=False)} ) as sub
            WHERE
                pv.product_id = sub.product_id AND
                pv.account_id = sub.account_id AND
                pv.valuation_area_id = sub.valuation_area_id AND
                pv.company_id = sub.company_id
        """

        self.env.cr.execute(sql, params)

    def _get_sql_select(self, all_records=True):
        sql = f"""
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
               {self._get_sql_sub_select(all_records)}
                ) as sub
             GROUP BY  product_id, valuation_area_id, account_id, company_id

        """
        return sql

    def _get_sql_sub_select(self, all_records=True):
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
        if not all_records:
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

        # sql = (
        #     """
        #     INSERT INTO product_valuation
        #         (product_id, valuation_area_id, account_id, company_id,
        #         quantity, quantity_in, quantity_out, debit, credit, amount)
        #     select product_id, valuation_area_id, account_id, company_id,
        #                  quantity, quantity_in, quantity_out, debit, credit, debit-credit as amount
        #     FROM ( %s ) as a
        #     """
        #     % self._get_sql_select()
        # )
        #

        self.env.cr.execute(
            """
            SELECT min(month) as min_month, max(month) as max_month
            FROM product_valuation_history
            """,
            params,
        )
        res = self.env.cr.dictfetchone()

        params["min_month"] = res.get("min_month", "202401")
        params["max_month"] = res.get("max_month", "202401")

        params["min_date"] = datetime.strptime(params["min_month"], "%Y%m")
        params["max_date"] = datetime.strptime(params["max_month"], "%Y%m")

        sql = """
        INSERT INTO product_valuation
                (product_id, valuation_area_id, account_id, company_id,
                quantity,  amount)
           SELECT product_id, valuation_area_id, account_id, company_id,
                         quantity_final as quantity, amount_final as amount
            FROM product_valuation_history as pv

            WHERE month = %(max_month)s
        """
        self.env.cr.execute(sql, params)


class ProductValuationHistory(models.Model):
    _name = "product.valuation.history"
    _description = "Product Valuation History"
    _inherit = ["product.valuation"]
    _order = "product_id, month desc"

    month = fields.Char(string="Month", required=True, index=True)

    amount_initial = fields.Monetary("Initial Amount", default=0.0)
    quantity_initial = fields.Float("Initial Quantity", digits="Product Unit of Measure", default=0.0)

    amount_final = fields.Monetary("Final Amount", compute="_compute_final", store=True, default=0.0)
    quantity_final = fields.Float(
        "Final Quantity", digits="Product Unit of Measure", compute="_compute_final", store=True, default=0.0
    )

    _sql_constraints = [
        (
            "product_valuation_history_uniq",
            "unique (product_id, valuation_area_id, account_id, company_id, month)",
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

        month = date.strftime("%Y%m")

        domain = [
            ("product_id", "=", product_id),
            ("valuation_area_id", "=", valuation_area_id),
            ("account_id", "=", account_id),
            ("company_id", "=", company_id),
            ("month", "=", month),
        ]
        valuation = self.search(domain, limit=1)
        if not valuation:
            last_valuation = self.search(
                [
                    ("product_id", "=", product_id),
                    ("valuation_area_id", "=", valuation_area_id),
                    ("account_id", "=", account_id),
                    ("company_id", "=", company_id),
                    ("month", "<", month),
                ],
                order="month desc",
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
                    "month": month,
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
                ("month", ">", s.month),
            ]
            next_valuation = self.search(domain, order="month asc", limit=1)
            if next_valuation:
                next_valuation.write(
                    {
                        "quantity_initial": s.quantity_final,
                        "amount_initial": s.amount_final,
                    }
                )

    def _compute_initial(self):
        for item in self:
            item.quantity_initial = item.quantity_final - item.quantity
            item.amount_initial = item.amount_final - item.amount
            domain = [
                ("product_id", "=", item.product_id.id),
                ("valuation_area_id", "=", item.valuation_area_id.id),
                ("account_id", "=", item.account_id.id),
                ("company_id", "=", item.company_id.id),
                ("month", "<", item.month),
            ]
            prev_valuation = self.search(domain, order="month desc", limit=1)
            if prev_valuation:
                prev_valuation.write(
                    {
                        "quantity_final": item.quantity_initial,
                        "amount_final": item.amount_initial,
                    }
                )
                prev_valuation._compute_initial()

    def _get_sql_select(self, all_records=True):
        """
            Determinare miscari lunare insumate
        :param all_records:
        :return:
        """
        sql = f"""
                    SELECT product_id, valuation_area_id, account_id, company_id, currency_id,   month,
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
                 {self._get_sql_sub_select(all_records)}
                ) as sub
             GROUP BY  product_id, valuation_area_id, account_id, company_id, currency_id,  month
        """
        return sql

    def _get_sql_sub_select(self, all_records=True):
        """
        Determinare miscari lunare
        """
        sql = """
            SELECT product_id, valuation_area_id, account_id, m.company_id, l.company_currency_id as currency_id,
                    debit, credit, move_type,
                    to_char(m.date, 'YYYYMM')  as month,

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
        if not all_records:
            sql += """
                    AND product_id in %(product_ids)s
                    AND account_id in %(account_ids)s
                    AND valuation_area_id in %(valuation_area_ids)s
                    AND to_char(m.date, 'YYYYMM') in %(month)s
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
            "month": tuple(self.mapped("month")),
            "company_ids": tuple(companies.ids),
            "valuation_area_ids": tuple(valuation_areas.ids) or (None,),
        }
        sql = f"""


           UPDATE product_valuation_history AS pv
            SET quantity = sub.quantity,
                quantity_in = sub.quantity_in,
                quantity_out = sub.quantity_out,
                debit = sub.debit,
                credit = sub.credit,
                amount = sub.debit - sub.credit
            FROM ( {self._get_sql_select(all_records=False)} ) as sub
            WHERE
                pv.product_id = sub.product_id AND
                pv.account_id = sub.account_id AND
                pv.valuation_area_id = sub.valuation_area_id AND
                pv.company_id = sub.company_id AND

                pv.month = sub.month
        """
        self.env.cr.execute(sql, params)
        # invalidate chashed fields
        self._invalidate_cache()
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

        sql = f"""
            INSERT INTO product_valuation_history
                (product_id, valuation_area_id, account_id, company_id, currency_id,  month,
                quantity, quantity_in, quantity_out, debit, credit, amount)
            SELECT product_id, valuation_area_id, account_id, company_id, currency_id,  month,
                        quantity, quantity_in, quantity_out, debit, credit, debit-credit as amount
            FROM ( {self._get_sql_select()} ) as a
        """

        self.env.cr.execute(sql, params)

        # optinere data minima si maxima
        self.env.cr.execute(
            """
            SELECT min(month) as min_month, max(month) as max_month
            FROM product_valuation_history
            WHERE valuation_area_id = %(valuation_area_id)s
            """,
            params,
        )
        res = self.env.cr.dictfetchone()

        params["max_month"] = res.get("max_month", "202401")
        params["min_month"] = res.get("min_month", "202401")
        params["min_date"] = datetime.strptime(params["min_month"], "%Y%m")
        params["max_date"] = datetime.strptime(params["max_month"], "%Y%m")

        compute_all = False

        if compute_all:
            _logger.info("Adaugare linii lipsa")
            self.env.cr.execute(
                """
                DROP TABLE IF EXISTS calendar_temporal;
                CREATE TEMP TABLE calendar_temporal AS
                SELECT
                     to_char(generate_series, 'YYYYMM') AS month
                FROM
                    generate_series(%(min_date)s::date, %(max_date)s::date, '1 month'::interval) ;

                INSERT INTO product_valuation_history
                (
                    product_id, valuation_area_id, account_id, company_id, currency_id,  month,
                    quantity, amount, quantity_initial, amount_initial, quantity_final, amount_final,
                    quantity_in, quantity_out, debit, credit
                )
                SELECT
                    p.product_id,
                    %(valuation_area_id)s as valuation_area_id,
                    a.account_id,
                    %(company_id)s as company_id,
                    %(currency_id)s as currency_id,

                    c.month AS month,
                    0 as quantity,
                    0 as amount,
                    0 as quantity_initial,
                    0 as amount_initial,
                    0 as quantity_final,
                    0 as amount_final,
                    0 as quantity_in,
                    0 as quantity_out,
                    0 as debit,
                    0 as credit


                FROM
                    calendar_temporal c
                CROSS JOIN (SELECT DISTINCT product_id FROM product_valuation_history) p
                CROSS JOIN (SELECT DISTINCT account_id FROM product_valuation_history) a
                ON CONFLICT (product_id, valuation_area_id, account_id, company_id, month) DO NOTHING


                """,
                params,
            )
            _logger.info("Liniile lipsa au fost adaugate")

        _logger.info("Calculare sold initial si final pentru ultima luna")
        self.env.cr.execute(
            """
                UPDATE product_valuation_history pv
                SET
                    amount_initial = svl.total_amount - pv.amount,
                    quantity_initial = svl.total_quantity - pv.quantity,
                    amount_final = svl.total_amount,
                    quantity_final = svl.total_quantity
                FROM (
                    SELECT svl.product_id,
                           SUM(svl.value) AS total_amount,
                           SUM(svl.quantity) AS total_quantity
                    FROM stock_valuation_layer svl
                    GROUP BY svl.product_id
                ) AS svl
                WHERE pv.product_id = svl.product_id AND
                      pv.month = %(max_month)s;
            """,
            params,
        )

        if compute_all:
            _logger.info("Calculare sold initial si final")
            self.env.cr.execute(
                """
                WITH final_values AS (
                SELECT
                        pvh.product_id,
                        pvh.valuation_area_id,
                        pvh.account_id,
                        pvh.company_id,
                        pvh.month,
                        pvh_last.amount_final - SUM(pvh.amount)
                            OVER (  PARTITION BY  pvh.product_id, pvh.valuation_area_id, pvh.account_id, pvh.company_id
                            ORDER BY pvh.month desc) AS cumulative_amount,
                        pvh_last.quantity_final - SUM(pvh.quantity)
                            OVER (PARTITION BY pvh.product_id, pvh.valuation_area_id, pvh.account_id, pvh.company_id
                            ORDER BY pvh.month desc) AS cumulative_quantity

                    FROM
                        product_valuation_history as pvh
                        JOIN product_valuation_history as pvh_last on
                            pvh.product_id = pvh_last.product_id and
                            pvh.valuation_area_id = pvh_last.valuation_area_id AND
                            pvh.account_id = pvh_last.account_id AND
                            pvh.company_id = pvh_last.company_id AND
                            pvh_last.month = %(max_month)s
                )
                UPDATE product_valuation_history pv
                SET
                    amount_initial = fv.cumulative_amount - fv.amount,
                    quantity_initial = fv.cumulative_quantity - fv.quantity,
                    amount_final = fv.cumulative_amount,
                    quantity_final = fv.cumulative_quantity
                FROM final_values fv
                WHERE
                    pv.product_id = fv.product_id AND
                    pv.valuation_area_id = fv.valuation_area_id AND
                    pv.account_id = fv.account_id AND
                    pv.company_id = fv.company_id AND
                    pv.month = fv.month AND
                    pv.month < %(max_month)s

                """
            )

        _logger.info("FINALIZARE CALCULARE ISTORIC VALORI")
        #
        #
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
                and (amount_final is null or amount_final = 0) ;
            """,
            params,
        )

        _logger.info("Calculare sold initial si final varianta Python")
        # # domain = [("valuation_area_id", "=", valuation_area.id), ("month", "=", res["max_month"])]
        # # valuations = self.search(domain)
        # # valuations._compute_initial()
