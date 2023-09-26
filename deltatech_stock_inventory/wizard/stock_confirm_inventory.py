# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockConfirmInventory(models.TransientModel):
    _name = "stock.confirm.inventory"
    _description = "Stock Confirm Inventory"

    product_tmpl_id = fields.Many2one("product.template")
    qty_available = fields.Float(related="product_tmpl_id.qty_available")
    last_inventory_date = fields.Date(
        string="Last Inventory Date",
        compute="_compute_last_inventory",
        readonly=True,
    )
    last_inventory_id = fields.Many2one(
        "stock.inventory",
        string="Last Inventory",
        compute="_compute_last_inventory",
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        defaults["product_tmpl_id"] = self.env.context.get("active_id", False)
        return defaults

    @api.depends("product_tmpl_id")
    def _compute_last_inventory(self):
        for product in self.product_tmpl_id.product_variant_ids:
            domain = [("product_id", "=", product.id), ("is_ok", "=", True)]
            line = self.env["stock.inventory.line"].search(domain, limit=1, order="id desc")
            self.last_inventory_id = line.inventory_id
            self.last_inventory_date = line.inventory_id.date

    def confirm_actual_inventory(self):
        products = self.product_tmpl_id.product_variant_ids
        inventory_values = {"state": "confirm", "line_ids": []}
        quants = self.env["stock.quant"].search([("product_id", "in", products.ids)])
        for quant in quants:
            if quant.location_id.usage == "internal" and (
                not quant.last_inventory_date
                or (quant.last_inventory_date and quant.last_inventory_date < fields.Date.today())
            ):
                values = {
                    "product_id": quant.product_id.id,
                    "product_uom_id": quant.product_id.uom_id.id,
                    "location_id": quant.location_id.id,
                    "theoretical_qty": quant.quantity,
                    "product_qty": quant.quantity,
                    "standard_price": quant.product_id.product_tmpl_id.standard_price,
                    "is_ok": True,
                }
                inventory_values["line_ids"].append((0, 0, values))
        if inventory_values["line_ids"]:
            inventory = self.env["stock.inventory"].create(inventory_values)
            inventory.action_validate()
