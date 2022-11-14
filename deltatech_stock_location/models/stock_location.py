# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import random
import string

from odoo import _, fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    source_location_id = fields.Many2one("stock.location", domain=[("usage", "=", "internal")])

    route_delivery_id = fields.Many2one("stock.location.route")
    delivery_picking_type_id = fields.Many2one("stock.picking.type", string="Delivery Operation")

    route_transfer_id = fields.Many2one("stock.location.route")
    transfer_picking_type_id = fields.Many2one("stock.picking.type", string="Transfer Operation")

    receipt_picking_type_id = fields.Many2one("stock.picking.type", string="Receipt Operation")

    def generate_route(self):
        for location in self:
            code = "".join(random.choices(string.ascii_letters, k=2))
            code = code.upper()
            primary_location = location.source_location_id
            warehouse_id = location.source_location_id.warehouse_id
            if not location.transfer_picking_type_id:
                picking_type = self.env["stock.picking.type"].create(
                    {
                        "name": _("Transfer to %s") % location.name,
                        "sequence_code": "TR" + code,
                        "code": "internal",
                        "default_location_src_id": primary_location.id,
                        "default_location_dest_id": location.id,
                        "warehouse_id": warehouse_id.id,
                    }
                )
                location.transfer_picking_type_id = picking_type

            if not location.delivery_picking_type_id:
                picking_type = self.env["stock.picking.type"].create(
                    {
                        "name": _("Delivery from %s") % location.name,
                        "sequence_code": "OUT" + code,
                        "code": "outgoing",
                        "default_location_src_id": location.id,
                        "default_location_dest_id": self.env.ref("stock.stock_location_customers").id,
                        "warehouse_id": warehouse_id.id,
                    }
                )
                location.delivery_picking_type_id = picking_type

            if not location.receipt_picking_type_id:
                picking_type = self.env["stock.picking.type"].create(
                    {
                        "name": _("Receipt to %s") % location.name,
                        "sequence_code": "IN" + code,
                        "code": "incoming",
                        "default_location_src_id": self.env.ref("stock.stock_location_suppliers").id,
                        "default_location_dest_id": location.id,
                        "warehouse_id": warehouse_id.id,
                    }
                )
                location.receipt_picking_type_id = picking_type

            if not location.route_delivery_id:
                route_name = _("Delivery from %s") % location.name

                route_delivery = self.env["stock.location.route"].create(
                    {
                        "name": route_name,
                        "sale_selectable": True,
                        "product_selectable": False,
                        "rule_ids": [
                            (
                                0,
                                0,
                                {
                                    "name": route_name,
                                    "action": "pull",
                                    "picking_type_id": location.delivery_picking_type_id.id,
                                    "location_src_id": location.id,
                                    "location_id": self.env.ref("stock.stock_location_suppliers").id,
                                    "procure_method": "mts_else_mto",
                                },
                            )
                        ],
                    }
                )

                location.route_delivery_id = route_delivery

            if not location.route_transfer_id:
                route_name = _("Transfer to %s") % location.name

                route_delivery = self.env["stock.location.route"].create(
                    {
                        "name": route_name,
                        "warehouse_selectable": True,
                        "product_selectable": False,
                        "warehouse_ids": [(4, warehouse_id.id)],
                        "rule_ids": [
                            (
                                0,
                                0,
                                {
                                    "name": route_name,
                                    "action": "pull",
                                    "picking_type_id": location.transfer_picking_type_id.id,
                                    "location_src_id": primary_location.id,
                                    "location_id": location.id,
                                    "procure_method": "make_to_stock",
                                },
                            )
                        ],
                    }
                )

                location.route_transfer_id = route_delivery
