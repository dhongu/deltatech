# ©  2008-2021 Deltatech
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
    purchase_price = fields.Float("Purchase price", readonly=False)
    sale_val = fields.Monetary(
        "Sale value", readonly=True, help="Sale value in company currency", currency_field="company_currency_id"
    )

    stock_val = fields.Monetary(
        "Stock value", readonly=True, help="Stock value in company currency", currency_field="company_currency_id"
    )
    profit_val = fields.Monetary(
        "Profit",
        readonly=True,
        help="Profit obtained at invoicing in company currency",
        currency_field="company_currency_id",
    )
    commission_computed = fields.Float("Commission Computed", readonly=True)
    commission_manager_computed = fields.Float("Commission Manager Computed", readonly=True)
    commission_director_computed = fields.Float("Commission Director Computed", readonly=True)

    commission = fields.Float("Commission")
    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    commercial_partner_id = fields.Many2one("res.partner", "Commercial Partner", readonly=True)

    user_id = fields.Many2one("res.users", "Salesperson")
    manager_user_id = fields.Many2one("res.users", "Sales Manager", readonly=True)
    director_user_id = fields.Many2one("res.users", "Sales Director", readonly=True)

    state_id = fields.Many2one("res.country.state", "Region", readonly=True)
    account_id = fields.Many2one("account.account", "Account", readonly=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    # period_id = fields.Many2one('account.period', 'Period', readonly=True)
    indicator_supplement = fields.Float("Supplement Indicator", readonly=True, digits=(12, 2), group_operator="avg")
    indicator_profit = fields.Float("Profit Indicator", readonly=True, digits=(12, 2), group_operator="avg")

    journal_id = fields.Many2one("account.journal", "Journal", readonly=True)
    company_currency_id = fields.Many2one("res.currency", "Currency", readonly=True, related="company_id.currency_id")
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)

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
    payment_state = fields.Selection(
        selection=[
            ("not_paid", "Not Paid"),
            ("in_payment", "In Payment"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
            ("reversed", "Reversed"),
            ("invoicing_legacy", "Invoicing App Legacy"),
        ],
        string="Payment Status",
        readonly=True,
    )

    def _select(self):
        select_str = """
            SELECT
                id, date, invoice_id, categ_id, product_id,  account_id, product_uom, product_uom_qty ,
                purchase_price,
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
                sub.director_rate * (sale_val    - stock_val )  as commission_director_computed,

                commission,
                partner_id, commercial_partner_id,  state_id, user_id, manager_user_id, director_user_id,   sub.company_id,
                move_type,  state , payment_state, journal_id,
                 sub.currency_id
        """
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT
                    l.id as id,
                    s.invoice_date as date,
                    l.move_id as invoice_id,
                    t.categ_id as categ_id,
                    l.product_id as product_id,
                    l.account_id as account_id,
                    t.uom_id as product_uom,


                    SUM(CASE
                     WHEN s.move_type::text = ANY (ARRAY['out_refund'::character varying::text,
                      'in_invoice'::character varying::text])
                        THEN -(l.quantity / u.factor * u2.factor)
                        ELSE  (l.quantity / u.factor * u2.factor)
                    END) AS product_uom_qty,

                    avg(purchase_price) as purchase_price,

                    SUM(-l.balance) AS sale_val,


                    SUM(CASE
                     WHEN s.move_type::text = ANY (ARRAY['out_refund'::character varying::text,
                     'in_invoice'::character varying::text])
                        THEN -(l.quantity * COALESCE( l.purchase_price, 0 ) )
                        ELSE  (l.quantity * COALESCE( l.purchase_price, 0 ) )
                    END) AS stock_val,


                    sum(l.commission) as commission,
                    cu.rate, cu.manager_rate, cu.director_rate, cu.manager_user_id, cu.director_user_id,

                    s.partner_id as partner_id,
                    s.commercial_partner_id as commercial_partner_id, res_partner.state_id,

                    s.company_id as company_id,
                    s.move_type, s.state , s.payment_state , s.journal_id, s.currency_id
        """
        get_param = self.env["ir.config_parameter"].sudo().get_param
        sale_user_detail = get_param("sale_commission.sale_user_detail", "invoice")

        if sale_user_detail == "invoice":
            select_str += ", s.invoice_user_id as user_id"
        else:
            select_str += ", l.sale_user_id as user_id"

        return select_str

    def _from(self):
        from_str = """
                    account_move s
                    left join account_move_line l on (s.id=l.move_id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join res_partner on (res_partner.id=s.partner_id)
                    left join uom_uom u on (u.id=l.product_uom_id)
                    left join uom_uom u2 on (u2.id=t.uom_id)

        """
        get_param = self.env["ir.config_parameter"].sudo().get_param
        sale_user_detail = get_param("sale_commission.sale_user_detail", "invoice")

        if sale_user_detail == "invoice":
            from_str += (
                " left join commission_users cu on (s.invoice_user_id = cu.user_id and cu.journal_id = s.journal_id)"
            )
        else:
            from_str += (
                " left join commission_users cu on (l.sale_user_id = cu.user_id and cu.journal_id = s.journal_id)"
            )
        return from_str

    def _where(self):
        where_str = """
              s.move_type in ( 'out_invoice', 'out_refund') and s.state='posted'
              and l.display_type = 'product'
        """
        return where_str

    def _group_by(self):
        group_by_str = """
                    l.id,
                    l.product_id,
                    l.account_id,
                    l.move_id,
                    t.uom_id,
                    t.categ_id,
                    s.invoice_date,
                    s.partner_id,
                    res_partner.state_id,
                    s.commercial_partner_id,
                    cu.rate,
                    cu.manager_rate,
                    cu.director_rate,
                    cu.manager_user_id,
                    cu.director_user_id,
                    s.company_id,

                    s.move_type,
                    s.state,
                    s.payment_state,
                    s.journal_id,
                    s.currency_id

        """
        get_param = self.env["ir.config_parameter"].sudo().get_param
        sale_user_detail = get_param("sale_commission.sale_user_detail", "invoice")

        if sale_user_detail == "invoice":
            group_by_str += "  , s.invoice_user_id"
        else:
            group_by_str += " , l.sale_user_id"
        return group_by_str

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
        invoice_line = self.env["account.move.line"].sudo().browse(self.id)
        value = {"commission": vals.get("commission", False)}
        if invoice_line.purchase_price == 0 and invoice_line.product_id:
            if invoice_line.product_id.standard_price > 0:
                value["purchase_price"] = invoice_line.product_id.standard_price
        if "purchase_price" in vals:
            value["purchase_price"] = vals.pop("purchase_price")
        invoice_line.write(value)
        if "user_id" in vals:
            invoice = self.env["account.move"].browse(self.invoice_id.id)
            invoice.write({"invoice_user_id": vals["user_id"]})
        if 1 == 2:
            super().write(vals)
        return True
