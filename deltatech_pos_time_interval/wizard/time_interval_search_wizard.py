from odoo import fields, models


class PosOrderTimePeriodWizard(models.TransientModel):
    _name = "pos.order.time.period.wizard"
    _description = "POS Order Time Period Wizard"

    start_date_1 = fields.Date(string="Start Date Interval 1", required=True)
    end_date_1 = fields.Date(string="End Date Interval 1", required=True)
    start_date_2 = fields.Date(string="Start Date Interval 2", required=True)
    end_date_2 = fields.Date(string="End Date Interval 2", required=True)

    def do_compute(self):
        # Clear existing data in the transient model
        self.env["pos.order.time.period.report"].search([]).unlink()

        # Fetch data for the first period
        first_period_lines = self.env["report.pos.order"].search(
            [("date", ">=", self.start_date_1), ("date", "<=", self.end_date_1)]
        )

        for line in first_period_lines:
            self.env["pos.order.time.period.report"].create(
                {
                    "date": line.date,
                    "order_id": line.order_id.id,
                    "partner_id": line.partner_id.id,
                    "product_id": line.product_id.id,
                    "product_tmpl_id": line.product_tmpl_id.id,
                    "state": line.state,
                    "user_id": line.user_id.id,
                    "price_total": line.price_total,
                    "price_sub_total": line.price_sub_total,
                    "total_discount": line.total_discount,
                    "average_price": line.average_price,
                    "company_id": line.company_id.id,
                    "nbr_lines": line.nbr_lines,
                    "product_qty": line.product_qty,
                    "journal_id": line.journal_id.id,
                    "delay_validation": line.delay_validation,
                    "product_categ_id": line.product_categ_id.id,
                    "invoiced": line.invoiced,
                    "config_id": line.config_id.id,
                    "pricelist_id": line.pricelist_id.id,
                    "session_id": line.session_id.id,
                    "margin": line.margin,
                    "time_period": f"{self.start_date_1} - {self.end_date_1}",
                }
            )

        # Fetch data for the second period
        second_period_lines = self.env["report.pos.order"].search(
            [("date", ">=", self.start_date_2), ("date", "<=", self.end_date_2)]
        )
        for line in second_period_lines:
            self.env["pos.order.time.period.report"].create(
                {
                    "date": line.date,
                    "order_id": line.order_id.id,
                    "partner_id": line.partner_id.id,
                    "product_id": line.product_id.id,
                    "product_tmpl_id": line.product_tmpl_id.id,
                    "state": line.state,
                    "user_id": line.user_id.id,
                    "price_total": line.price_total,
                    "price_sub_total": line.price_sub_total,
                    "total_discount": line.total_discount,
                    "average_price": line.average_price,
                    "company_id": line.company_id.id,
                    "nbr_lines": line.nbr_lines,
                    "product_qty": line.product_qty,
                    "journal_id": line.journal_id.id,
                    "delay_validation": line.delay_validation,
                    "product_categ_id": line.product_categ_id.id,
                    "invoiced": line.invoiced,
                    "config_id": line.config_id.id,
                    "pricelist_id": line.pricelist_id.id,
                    "session_id": line.session_id.id,
                    "margin": line.margin,
                    "time_period": f"{self.start_date_2} - {self.end_date_2}",
                }
            )

        return {
            "type": "ir.actions.act_window",
            "name": "POS Order Time Period Report",
            "res_model": "pos.order.time.period.report",
            "view_mode": "pivot",
            "view_id": self.env.ref("deltatech_pos_time_interval.view_pos_order_time_period_report_pivot").id,
            "target": "current",
        }


class PosOrderTimePeriodReport(models.TransientModel):
    _name = "pos.order.time.period.report"
    _description = "POS Order Time Period Report"

    date = fields.Datetime(string="Order Date", readonly=True)
    order_id = fields.Many2one("pos.order", string="Order", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Customer", readonly=True)
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", readonly=True)
    state = fields.Selection(
        [("draft", "New"), ("paid", "Paid"), ("done", "Posted"), ("invoiced", "Invoiced"), ("cancel", "Cancelled")],
        string="Status",
        readonly=True,
    )
    user_id = fields.Many2one("res.users", string="User", readonly=True)
    price_total = fields.Float(string="Total Price", readonly=True)
    price_sub_total = fields.Float(string="Subtotal w/o discount", readonly=True)
    total_discount = fields.Float(string="Total Discount", readonly=True)
    average_price = fields.Float(string="Average Price", readonly=True, aggregator="avg")
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    nbr_lines = fields.Integer(string="Sale Line Count", readonly=True)
    product_qty = fields.Integer(string="Product Quantity", readonly=True)
    journal_id = fields.Many2one("account.journal", string="Journal", readonly=True)
    delay_validation = fields.Integer(string="Delay Validation", readonly=True)
    product_categ_id = fields.Many2one("product.category", string="Product Category", readonly=True)
    invoiced = fields.Boolean(readonly=True)
    config_id = fields.Many2one("pos.config", string="Point of Sale", readonly=True)
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist", readonly=True)
    session_id = fields.Many2one("pos.session", string="Session", readonly=True)
    margin = fields.Float(string="Margin", readonly=True)
    time_period = fields.Char(string="Time Period", readonly=True)
