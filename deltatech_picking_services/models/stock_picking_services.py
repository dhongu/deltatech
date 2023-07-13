# ©  2008-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    picking_service_lines = fields.One2many("picking.service.line", "picking_id", string="Service Lines", copy=True)


class PickingServiceLine(models.Model):
    _name = "picking.service.line"
    _description = "Picking Service Line"
    _order = "sequence, id"

    sequence = fields.Integer("Sequence")
    product_id = fields.Many2one(
        "product.product",
        "Service",
        domain="[('type', '=', 'service')]",
        index=True,
        required=True,
    )
    product_uom = fields.Many2one(
        "uom.uom",
        "UoM",
        required=True,
        domain="[('category_id', '=', product_uom_category_id)]",
    )
    product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id")
    product_uom_qty = fields.Float(
        "Quantity",
        digits="Product Unit of Measure",
        default=1.0,
        required=True,
    )
    description_picking = fields.Char("Description")
    picking_id = fields.Many2one("stock.picking", "Transfer", index=True)
    price_unit = fields.Float("Unit Price", required=True, digits="Product Price", default=0.0)
    price_subtotal = fields.Float(compute="_compute_amount", string="Subtotal", store=True)

    @api.depends("product_uom_qty", "price_unit")
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.product_uom_qty

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            line.product_uom = line.product_id.uom_id
            line.description_picking = line.product_id.name
