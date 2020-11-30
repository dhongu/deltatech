# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models, tools


class SaleMarginReport(models.Model):
    _name = "sale.margin.report"
    _description = "Sale Margin Report"
    _auto = False
    _order = "date desc"

    date = fields.Date("Date", readonly=True)
    invoice_id = fields.Many2one("account.move", "Invoice", readonly=True)
    categ_id = fields.Many2one("product.category", "Category", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    product_uom = fields.Many2one("uom.uom", "Unit of Measure", readonly=True)
    product_uom_qty = fields.Float("Quantity", readonly=True)
    # 'purchase_price = fields.float('Purchase price', readonly=True )
    sale_val = fields.Float("Sale value", readonly=True, help="Sale value in company currency")

    stock_val = fields.Float("Stock value", readonly=True, help="Stock value in company currency")
    profit_val = fields.Float("Profit", readonly=True, help="Profit obtained at invoicing in company currency")
    commission_computed = fields.Float("Commission Computed", readonly=True)
    commission_manager_computed = fields.Float("Commission Manager Computed", readonly=True)
    commission = fields.Float("Commission")
    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    commercial_partner_id = fields.Many2one("res.partner", "Commercial Partner", readonly=True)
    user_id = fields.Many2one("res.users", "Salesperson")
    manager_user_id = fields.Many2one("res.users", "Sale manager", readonly=True)

    company_id = fields.Many2one("res.company", "Company", readonly=True)

    # period_id = fields.Many2one('account.period', 'Period', readonly=True)
    indicator_supplement = fields.Float("Supplement Indicator", readonly=True, digits=(12, 2), group_operator="avg")
    indicator_profit = fields.Float("Profit Indicator", readonly=True, digits=(12, 2), group_operator="avg")

    journal_id = fields.Many2one("account.journal", "Journal", readonly=True)
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    currency_rate = fields.Float("Currency Rate", readonly=True)

    move_type = fields.Selection(
        [
            ("out_invoice", "Customer Invoice"),
            ("in_invoice", "Vendor Bill"),
            ("out_refund", "Customer Refund"),
            ("in_refund", "Vendor Refund"),
        ],
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted"), ("cancel", "Cancelled")], string="Invoice Status", readonly=True
    )

    def _select(self):

        select_str = """
            SELECT
                id, date, invoice_id, categ_id, product_id, product_uom, product_uom_qty ,
                sale_val ,
                stock_val  as stock_val,
                (sale_val  - stock_val ) as profit_val,

                CASE
                     WHEN (stock_val ) = 0
                      THEN 0
                      ELSE  100 * (sale_val    - stock_val ) / stock_val
                END  AS indicator_supplement,

                CASE
                     WHEN (sale_val  ) = 0
                      THEN 0
                      ELSE  100 * (sale_val   - stock_val ) / (sale_val  )
                END  AS indicator_profit,


                sub.rate * (sale_val  - stock_val ) as commission_computed,
                sub.manager_rate * (sale_val    - stock_val )  as commission_manager_computed,
                commission,
                partner_id, commercial_partner_id, user_id, manager_user_id,     sub.company_id,
                move_type,  state ,  journal_id,
                cr.rate as currency_rate,
                 sub.currency_id
        """
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT
                    min(l.id) as id,
                    s.invoice_date as date,
                    l.move_id as invoice_id,
                    t.categ_id as categ_id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,


                    SUM(CASE
                     WHEN s.move_type::text = ANY (ARRAY['out_refund'::character varying::text,
                      'in_invoice'::character varying::text])
                        THEN -(l.quantity / u.factor * u2.factor)
                        ELSE  (l.quantity / u.factor * u2.factor)
                    END) AS product_uom_qty,

                    SUM(l.price_subtotal) AS sale_val,

                    SUM(CASE
                     WHEN s.move_type::text = ANY (ARRAY['out_refund'::character varying::text,
                     'in_invoice'::character varying::text])
                        THEN -(l.quantity * COALESCE( l.purchase_price, 0 ) )
                        ELSE  (l.quantity * COALESCE( l.purchase_price, 0 ) )
                    END) AS stock_val,


                    sum(l.commission) as commission,
                    cu.rate, cu.manager_rate, cu.manager_user_id,

                    s.partner_id as partner_id,
                    s.commercial_partner_id as commercial_partner_id,
                    s.invoice_user_id as user_id,

                    s.company_id as company_id,
                    s.move_type, s.state , s.journal_id, s.currency_id
        """

        # x = """
        # SUM(CASE
        #              WHEN s.type::text = ANY (ARRAY['out_refund'::character varying::text,
        #              'in_invoice'::character varying::text])
        #                 THEN -(l.quantity * l.price_unit_without_taxes * (100.0-COALESCE( l.discount, 0 )) / 100.0)
        #                 ELSE  (l.quantity * l.price_unit_without_taxes * (100.0-COALESCE( l.discount, 0 )) / 100.0)
        #             END) AS sale_val,
        # """
        return select_str

    def _from(self):
        from_str = """
                    account_move s
                    left join account_move_line l on (s.id=l.move_id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=l.product_uom_id)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                    left join commission_users cu on (s.invoice_user_id = cu.user_id)

        """
        return from_str

    def _where(self):
        where_str = """
              s.move_type in ( 'out_invoice', 'out_refund') and s.state in ( 'open','paid')
        """
        return where_str

    def _group_by(self):
        group_by_str = """
                    l.product_id,
                    l.move_id,
                    t.uom_id,
                    t.categ_id,
                    s.invoice_date,
                    s.partner_id,
                    s.commercial_partner_id,
                    s.invoice_user_id,
                    cu.rate,
                    cu.manager_rate,
                    cu.manager_user_id,
                    s.company_id,

                    s.move_type,
                    s.state,
                    s.journal_id,
                    s.currency_id

        """
        return group_by_str

    # '''
    # @api.model_cr
    # def init(self):
    #     # self._table = sale_report
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     # CREATE MATERIALIZED VIEW
    #     # CREATE or REPLACE VIEW
    #     sql = """CREATE or REPLACE VIEW %s as (
    #         WITH currency_rate (currency_id, rate, date_start, date_end) AS (
    #             SELECT r.currency_id, r.rate, r.name AS date_start,
    #                 (SELECT name FROM res_currency_rate r2
    #                  WHERE r2.name > r.name AND
    #                        r2.currency_id = r.currency_id
    #                  ORDER BY r2.name ASC
    #                  LIMIT 1) AS date_end
    #             FROM res_currency_rate r
    #         )
    #         %s
    #         FROM
    #         (
    #             %s
    #             FROM %s
    #             WHERE %s
    #             GROUP BY %s
    #         ) AS sub
    #         JOIN currency_rate cr ON
    #             (cr.currency_id = sub.currency_id AND
    #              cr.date_start <= COALESCE(sub.date, NOW()) AND
    #              (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date, NOW())))
    #     )"""
    #     sql = sql % (self._table,
    #                  self._select(), self._sub_select(), self._from(), self._where(), self._group_by())
    #     # print sql
    #     self.env.cr.execute(sql)
    # '''

    def init(self):

        tools.drop_view_if_exists(self.env.cr, self._table)
        # pylint: disable=E8103
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s as (
            WITH currency_rate AS (%s)
            %s
            FROM (
                %s
                FROM %s
                WHERE %s
                GROUP BY %s
            ) AS sub
            LEFT JOIN currency_rate cr ON
                (cr.currency_id = sub.currency_id AND
                 cr.company_id = sub.company_id AND
                 cr.date_start <= COALESCE(sub.date, NOW()) AND
                 (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date, NOW())))
        )"""
            % (
                self._table,
                self.env["res.currency"]._select_companies_rates(),
                self._select(),
                self._sub_select(),
                self._from(),
                self._where(),
                self._group_by(),
            )
        )

    def write(self, vals):
        invoice_line = self.env["account.invoice.line"].browse(self.id)
        value = {"commission": vals.get("commission", False)}
        if invoice_line.purchase_price == 0 and invoice_line.product_id:
            if invoice_line.product_id.standard_price > 0:
                value["purchase_price"] = invoice_line.product_id.standard_price
        # if 'purchase_price' in vals:
        #    value['purchase_price'] = vals['purchase_price']
        invoice_line.write(value)
        if "user_id" in vals:
            invoice = self.env["account.invoice"].browse(self.invoice_id)
            invoice.write({"user_id": vals["user_id"]})
        super(SaleMarginReport, self).write(vals)
        return True
