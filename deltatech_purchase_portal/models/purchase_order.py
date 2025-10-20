# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    signed_by = fields.Char(string="Signed by", readonly=True, copy=False)
    signed_on = fields.Datetime(string="Signed on", readonly=True, copy=False)
    signature = fields.Binary(string="Signature", readonly=True, copy=False)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    vendor_note = fields.Text(string="Vendor Observation")
