from odoo import _, api, fields, models
from odoo.exceptions import UserError


class InvoiceWizard(models.TransientModel):
    _name = "transfer.product.to.product"
    _description = "Invoice Wizard"

    from_product_id = fields.Many2one("product.product", string="From Product")
    location_adjustment = fields.Many2one("stock.location", string="Adjustment Location")
    to_product_id = fields.Many2one("product.product", string="To Product")
    quantity = fields.Float(string="Quantity")
    location_id = fields.Many2one("stock.location", string="Adjusting Location")

    @api.onchange("from_product_id")
    def _onchange_from_product_id(self):
        if self.from_product_id:
            self.location_id = self.from_product_id.property_stock_inventory

    def action_confirm(self):
        warehouse = self.env["stock.warehouse"].search(
            [("view_location_id", "parent_of", self.location_adjustment.id)], limit=1
        )
        picking_type_id = self.env["stock.picking.type"].search(
            [("code", "=", "internal"), ("warehouse_id", "=", warehouse.id)], limit=1
        )
        if not picking_type_id:
            raise UserError(_("Make sure you have at least an internal picking type defined"))
        picking_id = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type_id.id,
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
                "picking_type_id": picking_type_id.id,
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

        picking_id.button_validate()
        picking_id2.button_validate()
