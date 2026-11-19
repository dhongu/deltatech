# ©  2025 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrderLineConfigDetails(models.TransientModel):
    _name = "sale.order.line.config.details"
    _description = "Sale Order Line Configuration Details"

    config_details = fields.Html(string="Config Details", readonly=True)
