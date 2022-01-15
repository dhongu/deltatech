# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import api, fields, models
from odoo.tools import float_compare

# Get the logger
_logger = logging.getLogger(__name__)


class StockQuantReport(models.TransientModel):
    _name = "stock.quant.report"
    _description = "Stock Quant Report"

    location_id = fields.Many2one("stock.location", string="Source Location", required=True)
    refresh_report = fields.Boolean("Refresh Report", default=True)
    lines_ids = fields.One2many("stock.quant.report.value", "report_id")
    partner_id = fields.Many2one("res.partner")
    pricelist_id = fields.Many2one("product.pricelist", string="Reseller Price List")
    show_thresholds = fields.Boolean("Show text instead of stock")
    stock_threshold_1 = fields.Float("1st threshold", default=5)
    stock_threshold_1_text = fields.Char("1st threshold text")
    stock_threshold_2 = fields.Float("2nd threshold", default=20)
    stock_threshold_2_text = fields.Char("2nd threshold text")
    stock_no_threshold_text = fields.Char("Above 2nd threshold text")

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist

    def compute_data_for_report(self):
        self.ensure_one()

        domain = [("free_qty", ">", 0)]
        products = self.env["product.product"].with_context(location=self.location_id.id).search(domain)

        lines_values = []

        for product in products:
            price_reseller = self.pricelist_id.get_product_price(product, product.free_qty, None)
            qty_text = False
            if self.show_thresholds and product.free_qty > 0.0:
                if (
                    float_compare(product.free_qty, self.stock_threshold_1, precision_rounding=product.uom_id.rounding)
                    <= 0
                ):
                    qty_text = self.stock_threshold_1_text
                elif (
                    float_compare(product.free_qty, self.stock_threshold_2, precision_rounding=product.uom_id.rounding)
                    <= 0
                ):
                    qty_text = self.stock_threshold_2_text
                else:
                    qty_text = self.stock_no_threshold_text
            lines_values += [
                {
                    "report_id": self.id,
                    "description": product.description,
                    "product_id": product.id,
                    "qty": product.free_qty,
                    "qty_text": qty_text,
                    "categ_id": product.categ_id.id,
                    "list_price": product.list_price,
                    "list_currency_id": product.currency_id.id,
                    "price_reseller": price_reseller,
                    "reseller_currency_id": self.pricelist_id.currency_id.id,
                }
            ]

        self.env["stock.quant.report.value"].create(lines_values)

    def show_report(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "deltatech_stock_reseller.action_stock_quant_report_value"
        )
        action["domain"] = [("report_id", "=", self.id)]
        return action

    def do_execute(self):
        domain = [("location_id", "=", self.location_id.id), ("id", "!=", self.id)]
        if self.refresh_report:
            report = self.env["stock.quant.report"].search(domain)
            report.unlink()
            report = False
        else:
            report = self.env["stock.quant.report"].search(domain, limit=1)

        if not report:
            self.compute_data_for_report()
            report = self

        return report.show_report()


class StockQuantReportValue(models.TransientModel):
    _name = "stock.quant.report.value"
    _description = "Stock Quant Report"

    report_id = fields.Many2one("stock.quant.report", ondelete="cascade", string="Report")
    product_id = fields.Many2one("product.product", readonly=True, string="Product")

    qty = fields.Float(
        "Quantity",
        index=True,
        readonly=True,
        required=True,
        help="Quantity of products in this quant, in the default unit of measure of the product",
    )

    qty_text = fields.Char()
    product_uom_id = fields.Many2one("uom.uom", string="Unit of Measure", related="product_id.uom_id", readonly=True)

    categ_id = fields.Many2one("product.category", string="Internal Category", readonly=True)

    list_price = fields.Monetary("List Price", currency_field="list_currency_id")
    price_reseller = fields.Monetary("Reseller price", currency_field="reseller_currency_id")

    list_currency_id = fields.Many2one("res.currency")
    reseller_currency_id = fields.Many2one("res.currency")

    description = fields.Char()
