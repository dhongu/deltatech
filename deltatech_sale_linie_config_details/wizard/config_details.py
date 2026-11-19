# ©  2025 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrderLineConfigDetails(models.TransientModel):
    _name = "sale.order.line.config.details"
    _description = "Sale Order Line Configuration Details"

    # the HTML is built by sale.order.line.get_html_config_details, with every value escaped; the
    # style is kept so that the pictures keep their size
    config_details = fields.Html(string="Config Details", readonly=True, sanitize_style=True)
