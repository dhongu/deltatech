# ©  2015-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # the delivery status is standard since Odoo 16 (sale_stock, in sale since 20);
    # keep its changes in the chatter, as the former picking_status did
    delivery_status = fields.Selection(tracking=True)
