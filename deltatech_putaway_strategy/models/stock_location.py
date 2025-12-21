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
    )

    current_products = fields.Float(
        string="Current quantity",
        compute="_compute_warehouse_occupancy",
        help=(
            "Current quantity on hand. For leaves, computed as the sum of quantities "
            "from stock quants (quantity > 0). For non-leaves, sum of children."
        ),
        digits=(16, 2),
    )

    occupancy_ratio = fields.Float(
        string="Occupancy",
        compute="_compute_warehouse_occupancy",
        help="Occupancy ratio = current/max. 0 when max is 0.",
        digits=(16, 4),
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
        if not can_be_used:
            return False

        if self.max_products_leaf:
            # Capacitate pe frunză: nu depășim max_products_leaf
            if (self.current_products + quantity) > self.max_products_leaf:
                return False

        return True

    def _get_putaway_strategy(self, product, quantity=0, package=None, packaging=None, additional_qty=None):
        putaway_location = super()._get_putaway_strategy(product, quantity, package, packaging, additional_qty)

        # Dacă a ales locația curentă care are copii, încercăm să coborâm pe copii
        if putaway_location == self and putaway_location.child_ids:
            for child in self.child_ids:
                putaway_location = child._get_putaway_strategy(product, quantity, package, packaging, additional_qty)
                if putaway_location._check_can_be_used(product, quantity, package):
                    if not putaway_location.current_products:  # preferă locațiile goale
                        break
        return putaway_location
