# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductInvoiceHistory(models.TransientModel):
    _name = "product.invoice.history"
    _description = "product.invoice.history"

    template_id = fields.Many2one("product.template")
    year = fields.Char(string="Year")
    qty_in = fields.Float(string="Qty In", digits="Product Unit of Measure")
    qty_out = fields.Float(string="Qty Out", digits="Product Unit of Measure")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    invoice_history = fields.One2many("product.invoice.history", "template_id")
    last_sale_date = fields.Date()
    last_invoice_history_computed = fields.Datetime(string="Last Computed Invoice History")

    def refresh_invoice_history(self):
        self._compute_invoice_history_sql()

    def _compute_invoice_history_sql(self):
        template_ids = self.ids
        if not template_ids:
            query = """
                DELETE FROM product_invoice_history ;
                INSERT INTO product_invoice_history (template_id, year, qty_in, qty_out)
                SELECT
                    pp.product_tmpl_id as template_id,
                    EXTRACT(YEAR FROM aml.date) AS year,
                    SUM(CASE WHEN am.move_type IN ('in_invoice', 'in_refund') THEN aml.quantity ELSE 0 END) AS qty_in,
                    SUM(CASE WHEN am.move_type IN ('out_invoice', 'out_refund') THEN aml.quantity ELSE 0 END) AS qty_out
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN product_product pp ON aml.product_id = pp.id
                WHERE am.state='posted' or am.payment_state='invoicing_legacy'
                GROUP BY pp.product_tmpl_id, year
            """
        else:
            query = """
                DELETE FROM product_invoice_history WHERE template_id IN %s;
                INSERT INTO product_invoice_history (template_id, year, qty_in, qty_out)
                SELECT
                    pp.product_tmpl_id as template_id,
                    EXTRACT(YEAR FROM aml.date) AS year,
                    SUM(CASE WHEN am.move_type IN ('in_invoice', 'in_refund') THEN aml.quantity ELSE 0 END) AS qty_in,
                    SUM(CASE WHEN am.move_type IN ('out_invoice', 'out_refund') THEN aml.quantity ELSE 0 END) AS qty_out
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN product_product pp ON aml.product_id = pp.id
                WHERE pp.product_tmpl_id IN %s
                AND (am.state='posted' or am.payment_state='invoicing_legacy')
                GROUP BY pp.product_tmpl_id, year
            """

        params = (tuple(template_ids), tuple(template_ids))
        self.env.cr.execute(query, params)

    def _compute_invoice_history(self):
        for template in self:
            products = template.product_variant_ids
            domain = [
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("product_id", "in", products.ids),
            ]
            groups_out = self.env["account.invoice.report"].read_group(
                domain=domain,
                fields=["quantity", "invoice_date"],
                groupby=["invoice_date:year"],
            )

            domain = [
                ("move_type", "in", ["in_invoice", "in_refund"]),
                ("product_id", "in", products.ids),
            ]
            groups_in = self.env["account.invoice.report"].read_group(
                domain=domain,
                fields=["quantity", "invoice_date"],
                groupby=["invoice_date:year"],
            )

            invoice_history = self.env["product.invoice.history"]
            history = {}
            for item in groups_out:
                history[item["invoice_date:year"]] = {
                    "template_id": template.id,
                    "year": item["invoice_date:year"],
                    "qty_out": item["quantity"],
                }

            for item in groups_in:
                if item["invoice_date:year"] in history:
                    history[item["invoice_date:year"]]["qty_in"] = -1 * item["quantity"]
                else:
                    history[item["invoice_date:year"]] = {
                        "template_id": template.id,
                        "year": item["invoice_date:year"],
                        "qty_in": -1 * item["quantity"],
                    }
            history_values = []
            for year in history:
                history_values += [history[year]]
            invoice_history = self.env["product.invoice.history"].create(history_values)
            template.invoice_history = invoice_history

    def _cron_invoice_history(self):
        self.refresh_invoice_history()

    def action_view_invoice(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_invoice_report_all")
        products = self.env["product.product"]
        for template in self:
            products |= template.product_variant_ids
        action["context"] = {
            "group_by": ["date:year"],
            "measures": ["product_qty", "price_average"],
            "col_group_by": ["move_type"],
            "group_by_no_leaf": 1,
            "search_disable_custom_filters": True,
        }
        action["domain"] = [
            ("move_type", "in", ["out_invoice", "out_refund"]),
            ("product_id", "in", products.ids),
        ]
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_view_invoice(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_invoice_report_all")
        action["context"] = {
            "group_by": ["date:year"],
            "measures": ["product_qty", "price_average"],
            "col_group_by": ["move_type"],
            "group_by_no_leaf": 1,
            "search_disable_custom_filters": True,
        }

        action["domain"] = [
            ("move_type", "in", ["out_invoice", "out_refund"]),
            ("product_id", "in", self.ids),
        ]
        return action
