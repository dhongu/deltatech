# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductWarehouseLocation(models.Model):
    _name = "product.warehouse.location"
    _description = "Product Warehouse Location"

    product_id = fields.Many2one("product.template", index=True)
    warehouse_id = fields.Many2one("stock.warehouse", index=True)
    loc_rack = fields.Char("Rack", size=16)
    loc_row = fields.Char("Row", size=16)
    loc_shelf = fields.Char("Shelf", size=16)
    loc_case = fields.Char("Case", size=16)

    _sql_constraints = [
        ("product_product_uniq", "unique(product_id, warehouse_id)", "Warehouse must be unique per product!"),
    ]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    loc_rack = fields.Char("Rack", size=16, compute="_compute_loc", inverse="_inverse_loc")
    loc_row = fields.Char("Row", size=16, compute="_compute_loc", inverse="_inverse_loc")
    loc_shelf = fields.Char("Shelf", size=16, compute="_compute_loc", inverse="_inverse_loc")
    loc_case = fields.Char("Case", size=16, compute="_compute_loc", inverse="_inverse_loc")

    warehouse_loc_ids = fields.One2many("product.warehouse.location", "product_id")

    def _compute_loc(self):
        warehouse_id = self.env.context.get("warehouse", False)
        location_id = self.env.context.get("location", False)
        if not warehouse_id and location_id:
            if isinstance(location_id, int):
                location = self.env["stock.location"].browse(location_id)
                warehouse_id = location.warehouse_id.id
        if not warehouse_id:
            warehouse_id = self.env.ref("stock.warehouse0").id

        for product in self:
            domain = [("product_id", "=", product.id), ("warehouse_id", "=", warehouse_id)]
            loc = self.env["product.warehouse.location"].sudo().search(domain, limit=1)
            product.loc_rack = loc.loc_rack
            product.loc_row = loc.loc_row
            product.loc_shelf = loc.loc_shelf
            product.loc_case = loc.loc_case

    def _inverse_loc(self):

        warehouse_id = self.env.context.get("warehouse", False)
        if not warehouse_id:
            warehouse_id = self.env.ref("stock.warehouse0").id
        for product in self:
            domain = [("product_id", "=", product.id), ("warehouse_id", "=", warehouse_id)]
            loc = self.env["product.warehouse.location"].sudo().search(domain)
            values = {
                "loc_rack": product.loc_rack,
                "loc_row": product.loc_row,
                "loc_shelf": product.loc_shelf,
                "loc_case": product.loc_case,
                "product_id": product.id,
                "warehouse_id": warehouse_id,
            }
            if loc:
                loc.write(values)
            else:
                self.env["product.warehouse.location"].sudo().create(values)

    def confirm_actual_inventory(self):
        products = self.env["product.product"]
        for template in self:
            products |= template.product_variant_ids

        products.confirm_actual_inventory()


class ProductProduct(models.Model):
    _inherit = "product.product"

    def confirm_actual_inventory(self):
        products = self
        inventory_values = {"state": "confirm", "line_ids": []}
        quants = self.env["stock.quant"].search([("product_id", "in", products.ids)])
        for quant in quants:
            if quant.location_id.usage == "internal" and (
                not quant.product_id.last_inventory_date
                or (quant.product_id.last_inventory_date and quant.product_id.last_inventory_date < fields.Date.today())
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
