# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockConfirmInventory(models.TransientModel):
    _name = "stock.confirm.inventory"
    _description = "Stock Confirm Inventory"

    location_id = fields.Many2one("stock.location", string="Location", domain="[('usage', '=', 'internal')]")
    product_tmpl_id = fields.Many2one("product.template")
    qty_available = fields.Float(compute="_compute_last_inventory")
    last_inventory_date = fields.Date(string="Last Inventory Date", compute="_compute_last_inventory")
    last_inventory_id = fields.Many2one("stock.inventory", string="Last Inventory", compute="_compute_last_inventory")

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        defaults["product_tmpl_id"] = self.env.context.get("active_id", False)
        active_model = self.env.context.get("active_model", False)
        if active_model and active_model == "product.product":
            product = self.env["product.product"].browse(defaults["product_tmpl_id"])
            defaults["product_tmpl_id"] = product.product_tmpl_id.id
        return defaults

    @api.onchange("product_tmpl_id", "location_id")
    def _onchange_product_tmpl_id(self):
        self.last_inventory_date = False
        self.last_inventory_id = False
        self.qty_available = 0
        self._compute_last_inventory()

    @api.depends("product_tmpl_id", "location_id")
    def _compute_last_inventory(self):
        for rec in self:
            for product in rec.product_tmpl_id.product_variant_ids:
                domain = [
                    ("product_id", "=", product.id),
                    ("is_ok", "=", True),
                    ("location_id", "=", rec.location_id.id),
                ]
                line = self.env["stock.inventory.line"].search(domain, limit=1, order="id desc")
                rec.last_inventory_id = line.inventory_id
                rec.last_inventory_date = line.inventory_id.date
                rec.qty_available = product.with_context(location=rec.location_id.id).qty_available

    def confirm_actual_inventory(self):
        products = self.product_tmpl_id.product_variant_ids

        quants = self.env["stock.quant"].search(
            [("product_id", "in", products.ids), ("location_id", "=", self.location_id.id)]
        )
        quants.action_confirm_inventory()
