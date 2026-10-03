# ©  2015-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # the receipt status is standard since Odoo 16 (purchase_stock, in purchase since 20);
    # keep its changes in the chatter, as the former picking_status intended
    receipt_status = fields.Selection(tracking=True)
