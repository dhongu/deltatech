# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models

import odoo.addons.decimal_precision as dp


class ProductInvoiceHistory(models.TransientModel):
    _name = "product.invoice.history"
    _description = "product.invoice.history"

    product_id = fields.Many2one("product.product")
    template_id = fields.Many2one("product.template")
    year = fields.Char(string="Year")
    qty_in = fields.Float(string="Qty In", digits=dp.get_precision("Product Unit of Measure"))
    qty_out = fields.Float(string="Qty Out", digits=dp.get_precision("Product Unit of Measure"))


class ProductTemplate(models.Model):
    _inherit = "product.template"

    invoice_count = fields.Integer(compute="_compute_invoice_count")
    invoice_history = fields.One2many("product.invoice.history", "template_id", compute="_compute_invoice_history")
    last_sale_date = fields.Date()

    @api.multi
    def _compute_invoice_history(self):
        for template in self:
            products = template.product_variant_ids
            domain = [
                ("type", "in", ["out_invoice", "out_refund"]),
                ("product_id", "in", products.ids),
            ]
            groups_out = self.env["account.invoice.report"].read_group(
                domain=domain, fields=["product_qty", "date"], groupby=["date:year"]
            )

            domain = [
                ("type", "in", ["in_invoice", "in_refund"]),
                ("product_id", "in", products.ids),
            ]
            groups_in = self.env["account.invoice.report"].read_group(
                domain=domain, fields=["product_qty", "date"], groupby=["date:year"]
            )

            invoice_history = self.env["product.invoice.history"]
            history = {}
            for item in groups_out:
                history[item["date:year"]] = {
                    "template_id": template.id,
                    "year": item["date:year"],
                    "qty_out": item["product_qty"],
                }

            for item in groups_in:
                if item["date:year"] in history:
                    history[item["date:year"]]["qty_in"] = -1 * item["product_qty"]
                else:
                    history[item["date:year"]] = {
                        "template_id": template.id,
                        "year": item["date:year"],
                        "qty_in": -1 * item["product_qty"],
                    }
            history_values = []
            for year in history:
                history_values += [history[year]]
            invoice_history = self.env["product.invoice.history"].create(history_values)
            template.invoice_history = invoice_history

    @api.multi
    def _compute_invoice_count(self):
        products = self.env["product.product"]
        for template in self:
            products = template.product_variant_ids

            domain = [
                ("type", "in", ["out_invoice", "out_refund"]),
                ("product_id", "in", products.ids),
            ]
            product_qty = 0
            price_average = 0.0
            groups = self.env["account.invoice.report"].read_group(
                domain=domain, fields=["product_id", "product_qty", "price_average"], groupby=["product_id"]
            )
            for item in groups:
                product_qty += item["product_qty"]
                price_average = item["price_average"]

            template.invoice_count = price_average

    @api.multi
    def action_view_invoice(self):

        action = self.env.ref("account.action_account_invoice_report_all").read()[0]
        products = self.env["product.product"]
        for template in self:
            products |= template.product_variant_ids
        action[
            "context"
        ] = """{
             'group_by':['date:year'],
             'measures': ['product_qty', 'price_average'],
             'col_group_by': ['type'] ,
              'group_by_no_leaf': 1,
              'search_disable_custom_filters': True
             }"""
        #
        action["domain"] = [("type", "in", ["out_invoice", "out_refund"]), ("product_id", "in", products.ids)]
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def action_view_invoice(self):
        action = self.env.ref("account.action_account_invoice_report_all").read()[0]
        action[
            "context"
        ] = """{
             'group_by':['date:year'],
             'measures': ['product_qty', 'price_average'],
             'col_group_by': ['type'] ,
              'group_by_no_leaf': 1,
              'search_disable_custom_filters': True
             }"""
        #
        action["domain"] = [("type", "in", ["out_invoice", "out_refund"]), ("product_id", "in", self.ids)]
        return action
