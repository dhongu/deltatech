# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    quote_id = fields.Many2one(
        "sale.order",
        string="Sale Quote",
        index=True,
        readonly=False,
        help="Related quote from which this RFQ/PO was initiated.",
        ondelete="set null",
    )
