# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    vendor_note = fields.Text(string="Vendor Observation")

