# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductWarehouseLocation(models.Model):
    _name = "product.warehouse.location"
    _description = "Product Warehouse Location"

    product_id = fields.Many2one("product.template")
    warehouse_id = fields.Many2one("stock.warehouse")
    loc_rack = fields.Char("Rack", size=16)
    loc_row = fields.Char("Row", size=16)
    loc_case = fields.Char("Case", size=16)

    _sql_constraints = [
        ("product_product_uniq", "unique(product_id, warehouse_id)", "Warehouse must be unique per product!"),
    ]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    loc_rack = fields.Char("Rack", size=16, compute="_compute_loc", inverse="_inverse_loc")
    loc_row = fields.Char("Row", size=16, compute="_compute_loc", inverse="_inverse_loc")
    loc_case = fields.Char("Case", size=16, compute="_compute_loc", inverse="_inverse_loc")

    warehouse_loc_ids = fields.One2many("product.warehouse.location", "product_id")

    last_inventory_date = fields.Date(
        string="Last Inventory Date", readonly=True, compute="_compute_last_inventory", store=True
    )
    last_inventory_id = fields.Many2one(
        "stock.inventory", string="Last Inventory", readonly=True, compute="_compute_last_inventory", store=True
    )

    def _compute_loc(self):
        warehouse_id = self.env.context.get("warehouse", False)
        if not warehouse_id:
            warehouse_id = self.env.ref("stock.warehouse0").id

        for product in self:
            domain = [("product_id", "=", product.id), ("warehouse_id", "=", warehouse_id)]
            loc = self.env["product.warehouse.location"].sudo().search(domain, limit=1)
            product.loc_rack = loc.loc_rack
            product.loc_row = loc.loc_row
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
                "loc_case": product.loc_case,
                "product_id": product.id,
                "warehouse_id": warehouse_id,
            }
            if loc:
                loc.write(values)
            else:
                self.env["product.warehouse.location"].sudo().create(values)

    @api.multi
    def get_last_inventory_date(self):
        products = self.env["product.product"]
        for template in self:
            products |= template.product_variant_ids
        products.get_last_inventory_date()

    @api.multi
    def _compute_last_inventory(self):
        for template in self:
            last_inventory_date = False
            last_inventory_id = False
            for product in template.product_variant_ids:
                if last_inventory_date < product.last_inventory_date:
                    last_inventory_date = product.last_inventory_date
                    last_inventory_id = product.last_inventory_id
            template.last_inventory_date = last_inventory_date
            template.last_inventory_id = last_inventory_id


class ProductProduct(models.Model):
    _inherit = "product.product"

    last_inventory_date = fields.Date(string="Last Inventory Date", readonly=True)
    last_inventory_id = fields.Many2one("stock.inventory", string="Last Inventory", readonly=True)

    @api.multi
    def get_last_inventory_date(self):
        for product in self:
            line = self.env["stock.inventory.line"].search(
                [("product_id", "=", product.id), ("is_ok", "=", True)], limit=1, order="id desc"
            )
            if line:
                line.set_last_last_inventory()
            product.write({"last_inventory_date": fields.Date.today()})
