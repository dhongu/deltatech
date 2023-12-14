# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


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

    @api.depends_context("warehouse", "location")
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


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def get_theoretical_quantity(
        self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, to_uom=None
    ):
        product_id = self.env["product.product"].browse(product_id)
        product_id.check_access_rights("read")
        product_id.check_access_rule("read")

        location_id = self.env["stock.location"].browse(location_id)
        lot_id = self.env["stock.lot"].browse(lot_id)
        package_id = self.env["stock.quant.package"].browse(package_id)
        owner_id = self.env["res.partner"].browse(owner_id)
        to_uom = self.env["uom.uom"].browse(to_uom)
        quants = self.env["stock.quant"]._gather(
            product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True
        )
        if lot_id:
            quants = quants.filtered(lambda q: q.lot_id == lot_id)
        theoretical_quantity = sum(quant.quantity for quant in quants)
        if to_uom and product_id.uom_id != to_uom:
            theoretical_quantity = product_id.uom_id._compute_quantity(theoretical_quantity, to_uom)
        return theoretical_quantity
