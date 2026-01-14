from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    # Capacitate pentru frunze setată manual
    max_products_leaf = fields.Integer(
        string="Max products (leaf)",
        help=(
            "For leaf locations, set the maximum number of products. "
            "For non-leaf locations, total capacity is computed as the sum of children."
        ),
    )

    max_products = fields.Integer(
        string="Max products",
        compute="_compute_warehouse_occupancy",
        help="Maximum number of products allowed in this location (sum of children for non-leaf locations).",
        recursive=True,
    )

    current_products = fields.Float(
        string="Current quantity",
        compute="_compute_warehouse_occupancy",
        help=(
            "Current quantity on hand. For leaves, computed as the sum of quantities "
            "from stock quants (quantity > 0). For non-leaves, sum of children."
        ),
        digits=(16, 2),
        recursive=True,
    )

    occupancy_ratio = fields.Float(
        string="Occupancy",
        compute="_compute_warehouse_occupancy",
        help="Occupancy ratio = current/max. 0 when max is 0.",
        digits=(16, 4),
        recursive=True,
    )

    @api.depends(
        "child_ids",
        "child_ids.max_products_leaf",
        "child_ids.max_products",
        "child_ids.current_products",
    )
    def _compute_warehouse_occupancy(self):
        """Optimized compute using batched read_group and bottom-up aggregation.

        - For leaf locations: perform a single read_group over all leaves in the batch
          to fetch current quantities from stock.quant (quantity > 0).
        - For parent locations: aggregate values from children in memory.
        """
        Quant = self.env["stock.quant"].sudo()

        if not self:
            return

        leaves = self.filtered(lambda l: not l.child_ids)
        parents = self - leaves

        qty_by_loc = {}
        if leaves:
            sums = Quant.read_group(
                [("location_id", "in", leaves.ids), ("quantity", ">", 0)],
                ["quantity:sum"],
                ["location_id"],
                lazy=False,
            )
            qty_by_loc = {rec["location_id"][0]: rec.get("quantity", 0.0) for rec in sums}

        for leaf in leaves:
            max_p = int(leaf.max_products_leaf or 0)
            cur_p = float(qty_by_loc.get(leaf.id, 0.0))
            ratio = (cur_p / max_p) if max_p else 0.0
            ratio = min(1.0, max(0.0, ratio))
            leaf.max_products = max_p
            leaf.current_products = cur_p
            leaf.occupancy_ratio = ratio

        if parents:
            for loc in parents.sorted(key=lambda l: len((l.parent_path or "").split("/")), reverse=True):
                max_p = sum(child.max_products for child in loc.child_ids if child.max_products > 0)
                cur_p = sum(child.current_products for child in loc.child_ids)
                ratio = (cur_p / max_p) if max_p else 0.0
                ratio = min(1.0, max(0.0, ratio))
                loc.max_products = max_p
                loc.current_products = cur_p
                loc.occupancy_ratio = ratio

    def _check_can_be_used(self, product, quantity=0, package=None, location_qty=0):
        can_be_used = super()._check_can_be_used(product, quantity, package, location_qty)
        if self.env.context.get("putaway_location_standard"):
            return can_be_used

        if not can_be_used:
            return False

        if self.max_products_leaf:
            # Capacitate pe frunză: nu depășim max_products_leaf
            if self.current_products >= self.max_products_leaf:
                return False

        return True

    def _get_putaway_strategy(self, product, quantity=0, package=None, packaging=None, additional_qty=None):
        putaway_location = super()._get_putaway_strategy(product, quantity, package, packaging, additional_qty)
        if self.env.context.get("putaway_location_standard"):
            return putaway_location
        if putaway_location == self and self.child_ids:
            quants = self.env["stock.quant"].search(
                [
                    ("product_id", "=", product.id),
                    ("location_id", "child_of", self.id),
                    ("location_id.usage", "=", "internal"),
                    ("quantity", ">", 0),
                ]
            )

            for quant in quants.sorted(key=lambda q: q.location_id.complete_name):
                candidate = quant.location_id
                if candidate._check_can_be_used(product, quantity, package):
                    return candidate

            leaf_locations = self.env["stock.location"].search(
                [
                    ("id", "child_of", self.id),
                    ("child_ids", "=", False),  # Esențial: găsește doar capătul ierarhiei
                    ("usage", "=", "internal"),
                    ("id", "!=", self.id),  # Excludem nodul curent
                ],
                order="complete_name asc",
            )

            for leaf in leaf_locations:
                if leaf._check_can_be_used(product, quantity, package):
                    if not leaf.quant_ids.filtered(lambda q: q.quantity > 0):
                        return leaf
                    putaway_location = leaf
                    break
        return putaway_location
