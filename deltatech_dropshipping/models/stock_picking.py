# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    partner_shipping_id = fields.Many2one(
        "res.partner", compute="_compute_delivery_address_id", string="Shipping address"
    )

    def _compute_delivery_address_id(self):
        for picking in self:
            if picking.picking_type_code == "outgoing":
                picking.partner_shipping_id = picking.partner_id
            else:
                picking.partner_shipping_id = picking.picking_type_id.warehouse_id.partner_id
                if picking.sale_id.partner_shipping_id:
                    picking.partner_shipping_id = picking.sale_id.partner_shipping_id
