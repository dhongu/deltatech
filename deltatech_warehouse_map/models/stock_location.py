from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    # Manual capacity for leaf nodes
    max_products_leaf = fields.Integer(
        string="Max products (leaf)",
        help="For leaf locations, set the maximum number of products. For non-leaf locations, total capacity is computed as the sum of children.",
    )

    max_products = fields.Integer(
        string="Max products",
        compute="_compute_warehouse_occupancy",
        help="Maximum number of products allowed in this location (sum of children for non-leaf locations).",
    )

    current_products = fields.Integer(
        string="Current products",
        compute="_compute_warehouse_occupancy",
        help="Current number of products. For leaves, computed from stock quants (distinct products with quantity > 0). For non-leaves, sum of children.",
    )

    occupancy_ratio = fields.Float(
        string="Occupancy",
        compute="_compute_warehouse_occupancy",
        help="Occupancy ratio = current/max. 0 when max is 0.",
        digits=(16, 4),
    )

    @api.depends("child_ids", "child_ids.max_products_leaf", "child_ids.max_products", "child_ids.current_products")
    def _compute_warehouse_occupancy(self):
        Quant = self.env["stock.quant"].sudo()
        for loc in self:
            if loc.child_ids:
                # Aggregate from children
                max_products = sum(child.max_products for child in loc.child_ids)
                current_products = sum(child.current_products for child in loc.child_ids)
            else:
                # Leaf: capacity from manual field
                max_products = int(loc.max_products_leaf or 0)
                # Current products: count distinct products in quants with qty > 0 at this location
                domain = [("location_id", "=", loc.id), ("quantity", ">", 0)]
                groups = Quant.read_group(domain, ["product_id"], ["product_id"])  # distinct products
                current_products = len(groups)

            ratio = 0.0
            if max_products and max_products > 0:
                ratio = min(1.0, max(0.0, (current_products or 0) / float(max_products)))

            loc.max_products = max_products
            loc.current_products = current_products
            loc.occupancy_ratio = ratio

    def action_open_map(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "name": "Warehouse Map",
            "target": "self",
            "url": f"/deltatech/warehouse_map/location/{self.id}",
        }
