# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from datetime import datetime, timedelta

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import SQL, Query


class SaleMarginReport(models.Model):
    _name = "sale.margin.report"
    _description = "Sale Margin Report"
    _auto = False
    _order = "date desc"

    date = fields.Date("Date", readonly=True)
    due_date = fields.Date("Due Date", readonly=True)
    invoice_id = fields.Many2one("account.move", "Invoice", readonly=True)
    payment_term_id = fields.Many2one("account.payment.term", "Payment Term", readonly=True)
    categ_id = fields.Many2one("product.category", "Category", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    product_uom = fields.Many2one("uom.uom", "Unit of Measure", readonly=True)
    product_uom_qty = fields.Float("Quantity", readonly=True)
    # in the product unit, like the quantity: the cost of the invoice line is in the unit of the line
    purchase_price = fields.Float("Purchase price", readonly=False)
    is_storable = fields.Boolean("Track Inventory", readonly=True)
    sale_val = fields.Monetary(
        "Sale Amount",
        readonly=True,
        help="Sale Amount in company currency",
        currency_field="company_currency_id",
        aggregator="sum",
    )

    stock_val = fields.Monetary(
        "Stock Amount",
        readonly=True,
        help="Stock Amount in company currency",
        currency_field="company_currency_id",
        aggregator="sum",
    )
    profit_val = fields.Monetary(
        "Profit Amount",
        readonly=True,
        help="Profit obtained at invoicing in company currency",
        currency_field="company_currency_id",
        aggregator="sum",
    )
    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    commercial_partner_id = fields.Many2one("res.partner", "Commercial Partner", readonly=True)

    user_id = fields.Many2one("res.users", "Salesperson")

    state_id = fields.Many2one("res.country.state", "Region", readonly=True)
    account_id = fields.Many2one("account.account", "Account", readonly=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    # period_id = fields.Many2one('account.period', 'Period', readonly=True)

    markup = fields.Float("Markup", readonly=True, digits=(12, 2), aggregator="avg")
    profit_margin = fields.Float("Profit Margin", readonly=True, digits=(12, 2), aggregator="avg")

    journal_id = fields.Many2one("account.journal", "Journal", readonly=True)
    company_currency_id = fields.Many2one(
        "res.currency", "Company Currency", readonly=True, related="company_id.currency_id"
    )
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)

    move_type = fields.Selection(
        [
            ("out_invoice", "Customer Invoice"),
            ("in_invoice", "Vendor Bill"),
            ("out_refund", "Customer Refund"),
            ("in_refund", "Vendor Refund"),
            ("out_receipt", "Sales Receipt"),
        ],
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted"), ("cancel", "Cancelled")],
        string="Invoice Status",
        readonly=True,
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
                id, date,due_date, invoice_id,payment_term_id, categ_id, product_id,  account_id, product_uom, product_uom_qty ,
                purchase_price, is_storable,
                sale_val ,
                stock_val  as stock_val,
                (sale_val  - stock_val ) as profit_val,

                CASE
                     WHEN (stock_val ) = 0
                      THEN 0
                      ELSE  100 * (sale_val    - stock_val ) / stock_val
                END  AS markup,

                CASE
                     WHEN (sale_val  ) = 0
                      THEN 0
                      ELSE  100 * (sale_val   - stock_val ) / (sale_val  )
                END  AS profit_margin,

                partner_id, commercial_partner_id,  state_id, user_id, sub.company_id,
                move_type,  state , payment_state, journal_id,
                 sub.currency_id
        """
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT
                    l.id as id,
                    s.invoice_date as date,
                    s.invoice_date_due as due_date,
                    s.invoice_payment_term_id as payment_term_id,
                    l.move_id as invoice_id,
                    t.categ_id as categ_id,
                    l.product_id as product_id,
                    l.account_id as account_id,
                    t.uom_id as product_uom,


                    -- quantity in the product unit: uom factors are absolute (Dozen = 12), so
                    -- line unit -> product unit is qty * u.factor / u2.factor, as in uom._compute_quantity;
                    -- a line without a unit or without a product keeps its quantity
                    SUM(CASE
                     WHEN s.move_type::text = ANY (ARRAY['out_refund'::character varying::text,
                      'in_invoice'::character varying::text])
                        THEN -(l.quantity * COALESCE(u.factor / NULLIF(u2.factor, 0), 1))
                        ELSE  (l.quantity * COALESCE(u.factor / NULLIF(u2.factor, 0), 1))
                    END) AS product_uom_qty,

                    -- the cost of the line is per line unit; per product unit it is
                    -- price * u2.factor / u.factor, as in uom._compute_price
                    avg(l.purchase_price * COALESCE(u2.factor / NULLIF(u.factor, 0), 1)) as purchase_price,

                    COALESCE(t.is_storable, false) as is_storable,

                    SUM(-l.balance) AS sale_val,


                    SUM(CASE
                     WHEN s.move_type::text = ANY (ARRAY['out_refund'::character varying::text,
                     'in_invoice'::character varying::text])
                        THEN -(l.quantity * COALESCE( l.purchase_price, 0 ) )
                        ELSE  (l.quantity * COALESCE( l.purchase_price, 0 ) )
                    END) AS stock_val,


                    s.partner_id as partner_id,
                    s.commercial_partner_id as commercial_partner_id, res_partner.state_id,

                    s.company_id as company_id,
                    s.move_type, s.state , s.payment_state , s.journal_id, s.currency_id
        """
        select_str += f", {self._user_column()} as user_id"
        return select_str

    def _user_column(self):
        """The salesperson of an invoice line in the sub-select: the one of the invoice."""
        return "s.invoice_user_id"

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
        return from_str

    def _where(self):
        where_str = """
              s.move_type in ( 'out_invoice', 'out_refund', 'out_receipt') and s.state='posted'
              and l.display_type in ('product','discount')
        """
        return where_str

    def _group_by(self):
        group_by_str = """
                    l.id,
                    l.product_id,
                    l.account_id,
                    l.move_id,
                    t.uom_id,
                    t.is_storable,
                    t.categ_id,
                    s.invoice_date,
                    s.invoice_date_due,
                    s.invoice_payment_term_id,
                    s.partner_id,
                    res_partner.state_id,
                    s.commercial_partner_id,
                    s.company_id,

                    s.move_type,
                    s.state,
                    s.payment_state,
                    s.journal_id,
                    s.currency_id

        """
        group_by_str += f", {self._user_column()}"
        return group_by_str

    @staticmethod
    def _sql_fragment(code):
        # the fragments are plain strings (also in the inheriting modules); SQL() reads "%" as a
        # placeholder, so a literal one (LIKE 'a%') has to be escaped
        return SQL(code.replace("%", "%%"))

    def _extra_sources(self):
        """Sales recorded elsewhere than on the invoices, added to the report with UNION ALL.

        Each source is a dict of plain strings, like the other fragments:

        - ``from``: the tables of the source, with their joins;
        - ``where``: the condition on them (optional);
        - ``columns``: {column of the sub-select: SQL expression};
        - ``user_column``, ``journal_column``, ``company_column``: the salesperson, the journal and
          the company of a row, for the extensions that join on them (the commission rates).

        The columns are put in the order of the invoice sub-select, by name, and a column the source
        does not give is NULL: the extensions that add a column to the invoices keep working, the
        column is only empty on the rows of the source. The ids of a source must be negative, the
        positive ones are the invoice lines, and its rows are read-only (see ``_invoice_rows``).
        """
        return []

    def _prepare_extra_source(self, source):
        """A source of ``_extra_sources()`` completed by the extensions, which add their joins and
        columns to every source (the commission rates). Called on each source when the view is
        built, so it does not depend on the order in which the modules of the sources are loaded."""
        return source

    def _invoice_query(self):
        return SQL(
            "%s FROM %s WHERE %s GROUP BY %s",
            self._sql_fragment(self._sub_select()),
            self._sql_fragment(self._from()),
            self._sql_fragment(self._where()),
            self._sql_fragment(self._group_by()),
        )

    def _sub_select_columns(self, currency_rate, invoice_query):
        """The (name, type) of the columns of the invoice sub-select, in their order."""
        cr = self.env.cr
        cr.execute(SQL("WITH currency_rate AS (%s) SELECT * FROM (%s) AS sub LIMIT 0", currency_rate, invoice_query))
        columns = [(column.name, column.type_code) for column in cr.description]
        cr.execute(
            SQL("SELECT oid, format_type(oid, NULL) FROM pg_type WHERE oid IN %s", tuple({oid for _, oid in columns}))
        )
        type_names = dict(cr.fetchall())
        return [(name, type_names[oid]) for name, oid in columns]

    def _extra_source_query(self, source, columns):
        return SQL(
            "SELECT %s FROM %s WHERE %s",
            SQL(", ").join(
                SQL(
                    "(%s)::%s AS %s",
                    self._sql_fragment(source["columns"].get(name, "NULL")),
                    SQL(type_name),
                    SQL.identifier(name),
                )
                for name, type_name in columns
            ),
            self._sql_fragment(source["from"]),
            self._sql_fragment(source.get("where") or "true"),
        )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        currency_rate = self._sql_fragment(self.env["res.currency"]._select_companies_rates())
        sub_query = self._invoice_query()
        sources = [self._prepare_extra_source(source) for source in self._extra_sources()]
        if sources:
            columns = self._sub_select_columns(currency_rate, sub_query)
            sub_query = SQL(" UNION ALL ").join(
                SQL("(%s)", query)
                for query in [sub_query, *(self._extra_source_query(source, columns) for source in sources)]
            )
        self.env.cr.execute(
            SQL(
                """CREATE or REPLACE VIEW %s as (
            WITH currency_rate AS (%s)
            %s
            FROM (
                %s
            ) AS sub
        )""",
                SQL.identifier(self._table),
                currency_rate,
                self._sql_fragment(self._select()),
                sub_query,
            )
        )

    def _invoice_rows(self):
        """The rows that are invoice lines; the rows of the other sources (negative ids) are read-only."""
        return self.filtered(lambda row: row.id > 0)

    def write(self, vals):  # pylint: disable=method-required-super
        # The report is a SQL view: super().write() would try to UPDATE the view, so the values
        # are routed to the invoice lines behind it. The lines are written with sudo because
        # the sales roles only read account.move.line; the access check below is what keeps the
        # write limited to the managers (the viewers have read-only access).
        self.check_access("write")
        if self != self._invoice_rows():
            raise UserError(self.env._("Only the lines of an invoice can be changed in the margin report."))
        value = {fname: vals[fname] for fname in self._invoice_line_fields() if fname in vals}
        invoice_lines = self.env["account.move.line"].sudo().browse(self.ids)
        if "purchase_price" in value:
            # the report shows the cost per product unit, the invoice line keeps it per line unit
            purchase_price = value.pop("purchase_price")
            for invoice_line in invoice_lines:
                product_uom = invoice_line.product_id.uom_id
                line_price = purchase_price
                if product_uom and invoice_line.product_uom_id and invoice_line.product_uom_id != product_uom:
                    line_price = product_uom._compute_price(purchase_price, invoice_line.product_uom_id)
                invoice_line.write({"purchase_price": line_price})
        if value:
            invoice_lines.write(value)
        if "user_id" in vals:
            self.invoice_id.write({"invoice_user_id": vals["user_id"]})
        invoice_lines.flush_recordset()
        self.invalidate_recordset()
        return True

    def _invoice_line_fields(self):
        """The fields of the report written as they are on the invoice lines behind it."""
        return ["purchase_price"]

    @api.model
    def cron_update_purchase_price(self):
        """Fill in the cost of the lines of the last week from the documents.

        The cost itself comes from ``_purchase_price_from_document()``, the single rule shared with
        the update wizard. What the two do with a 0 on a credit note differs, on purpose:

        - the wizard is run by hand by a manager on the lines he picked, so it *resets* the cost,
          0 included: that is how a credit note wrongly costed in the past gets corrected;
        - the cron runs unattended over everything invoiced in the last week, so it only *fills in*
          a cost the documents know, and never writes a 0. A credit note that a manager costed by
          hand — goods that came back without the return being recorded in stock, say — would
          otherwise be silently zeroed a day later, with no one watching.

        New credit notes get their 0 from the compute on the line anyway, so the cron would have
        almost nothing to correct here; it is not worth the risk of undoing manual work.
        """
        AccountMoveLine = self.env["account.move.line"].sudo()

        last_week = (datetime.now() - timedelta(days=7)).date()

        lines = self.env["sale.margin.report"].search([("date", ">=", last_week)])._invoice_rows()

        for line in lines:
            invoice_line = AccountMoveLine.browse(line.id)
            if not invoice_line:
                continue
            purchase_price = invoice_line._purchase_price_from_document()
            if purchase_price:
                invoice_line.write({"purchase_price": purchase_price})

        return True

    # Adăugați metoda _read_group_select pentru a personaliza calculul la grupare
    def _read_group_select(self, aggregate_spec: str, query: Query) -> SQL:
        if aggregate_spec == "markup:avg":
            # Calculează indicatorul de supliment din valorile agregate de vânzări și stoc
            sale_val_sql = self._read_group_select("sale_val:sum", query)
            stock_val_sql = self._read_group_select("stock_val:sum", query)
            sql_expr = SQL(
                "CASE WHEN %s = 0 THEN 0 ELSE 100 * (%s - %s) / %s END",
                stock_val_sql,
                sale_val_sql,
                stock_val_sql,
                stock_val_sql,
            )
            return sql_expr

        elif aggregate_spec == "profit_margin:avg":
            # Calculează indicatorul de profit din valorile agregate de vânzări și stoc
            sale_val_sql = self._read_group_select("sale_val:sum", query)
            stock_val_sql = self._read_group_select("stock_val:sum", query)
            sql_expr = SQL(
                "CASE WHEN %s = 0 THEN 0 ELSE 100 * (%s - %s) / %s END",
                sale_val_sql,
                sale_val_sql,
                stock_val_sql,
                sale_val_sql,
            )
            return sql_expr

        return super()._read_group_select(aggregate_spec, query)
