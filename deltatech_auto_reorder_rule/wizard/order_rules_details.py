from odoo import fields, models


class OrderRulesDetailsWizard(models.TransientModel):
    _name = "order.rules.details.wizard"
    _description = "Order Rules Details Wizard"

    min_quantity = fields.Float(string="Minimum Quantity", required=True)
    max_quantity = fields.Float(string="Maximum Quantity", required=True)
    stock_location_ids = fields.Many2many(
        comodel_name="stock.location", string="Stock Locations", help="Select stock locations for the order rules."
    )
    trigger = fields.Selection(
        [("auto", "Automatic"), ("manual", "Manual")], string="Trigger", required=True, default="manual"
    )

    def do_create(self):
        product_template = self.env["product.template"].browse(self._context.get("active_id"))
        values = []
        for variant in product_template.product_variant_ids:
            for location in self.stock_location_ids:
                values.append(
                    {
                        "product_id": variant.id,
                        "product_min_qty": self.min_quantity,
                        "product_max_qty": self.max_quantity,
                        "qty_multiple": 0,
                        "trigger": self.trigger,
                        "location_id": location.id,
                    }
                )
        if values:
            self.env["stock.warehouse.orderpoint"].create(values)
