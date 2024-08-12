from odoo import _, api, fields, models
from odoo.exceptions import UserError


class InvoiceWizard(models.TransientModel):
    _name = "transfer.product.to.product"
    _description = "Transfer Wizard"

    from_product_id = fields.Many2one("product.product", string="From Product", required=True)
    location_adjustment = fields.Many2one("stock.location", string="Adjustment Location", required=True)
    to_product_id = fields.Many2one("product.product", string="To Product", required=True)
    quantity = fields.Float(string="Quantity", required=True, default=1.0)
    location_id = fields.Many2one("stock.location", string="Adjusting Location", required=True)
    operation_type = fields.Many2one(
        "stock.picking.type", string="Operation Type", domain=[("code", "=", "internal")], required=True
    )
    price_state = fields.Selection(
        [("draft", "draft"), ("equal", "equal"), ("different", "different")], default="draft"
    )
    alert_message = fields.Char()

    @api.onchange("from_product_id", "to_product_id")
    def _onchange_product_id(self):
        if self.from_product_id and self.to_product_id:
            if self.from_product_id.standard_price == self.to_product_id.standard_price:
                self.price_state = "equal"
                self.alert_message = "The price of the products is the same"
            else:
                self.price_state = "different"
                self.alert_message = (
                    "Careful! "
                    + self.from_product_id.name
                    + " costs "
                    + str(self.from_product_id.standard_price)
                    + " and "
                    + self.to_product_id.name
                    + " costs "
                    + str(self.to_product_id.standard_price)
                )
        else:
            self.price_state = "draft"
            self.alert_message = ""

    @api.onchange("from_product_id")
    def _onchange_from_product_id(self):
        if self.from_product_id:
            self.location_id = self.from_product_id.property_stock_inventory

    @api.onchange("location_adjustment")
    def _onchange_location_adjustment(self):
        if self.location_adjustment:
            warehouse = self.env["stock.warehouse"].search(
                [("view_location_id", "parent_of", self.location_adjustment.id)], limit=1
            )
            picking_type_id = self.env["stock.picking.type"].search(
                [("code", "=", "internal"), ("warehouse_id", "=", warehouse.id)], limit=1
            )
            if not picking_type_id:
                raise UserError(_("You don't have internal picking type defined for this warehouse"))
            else:
                self.operation_type = picking_type_id.id

    def action_confirm(self):
        picking_id = self.env["stock.picking"].create(
            {
                "picking_type_id": self.operation_type.id,
                "location_id": self.location_adjustment.id,
                "location_dest_id": self.location_id.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": self.from_product_id.name,
                "product_id": self.from_product_id.id,
                "product_uom_qty": self.quantity,
                "product_uom": self.from_product_id.uom_id.id,
                "picking_id": picking_id.id,
                "location_id": self.location_adjustment.id,
                "location_dest_id": self.location_id.id,
            }
        )

        picking_id2 = self.env["stock.picking"].create(
            {
                "picking_type_id": self.operation_type.id,
                "location_id": self.location_id.id,
                "location_dest_id": self.location_adjustment.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": self.to_product_id.name,
                "product_id": self.to_product_id.id,
                "product_uom_qty": self.quantity,
                "product_uom": self.to_product_id.uom_id.id,
                "picking_id": picking_id2.id,
                "location_id": self.location_id.id,
                "location_dest_id": self.location_adjustment.id,
            }
        )

        # Confirm the pickings to reserve the products
        picking_id.action_confirm()
        picking_id2.action_confirm()

        # Validate the pickings
        picking_id.button_validate()
        picking_id2.button_validate()
