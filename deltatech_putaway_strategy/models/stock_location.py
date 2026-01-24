from odoo import fields, models


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

    planned_products = fields.Float(
        string="Planned quantity",
        compute="_compute_planned_products",
        help=(
            "Planned quantity (incoming). For leaves, computed as the sum of quantities "
            "from stock moves not done or cancelled. For non-leaves, sum of children."
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

    def _compute_planned_products(self):
        Move = self.env["stock.move"].sudo()
        MoveLine = self.env["stock.move.line"].sudo()
        if not self:
            return

        leaves = self.filtered(lambda l: not l.child_ids)
        parents = self - leaves

        planned_qty_by_loc = {}
        if leaves:
            # Mișcări de stoc care nu sunt finalizate (planificate)
            # Luăm în calcul atât stock.move cât și stock.move.line care nu au move_id sau sunt legate de move-uri active
            # Dar cel mai sigur este să ne uităm la move_line-urile care nu sunt încă 'done' sau 'cancel'

            # 1. Cantități din stock.move (pentru cele care nu au încă move lines detaliate sau sunt în stare de așteptare)
            planned_sums = Move.read_group(
                [
                    ("location_dest_id", "in", leaves.ids),
                    ("state", "not in", ["done", "cancel"]),
                    ("location_id", "!=", "location_dest_id"),
                ],
                ["product_uom_qty:sum"],
                ["location_dest_id"],
                lazy=False,
            )
            for rec in planned_sums:
                loc_id = rec["location_dest_id"][0]
                planned_qty_by_loc[loc_id] = planned_qty_by_loc.get(loc_id, 0.0) + rec.get("product_uom_qty", 0.0)

            # 2. Cantități din stock.move.line (pentru cele care au deja locații de destinație specifice)
            # Dacă un move are move_lines, product_uom_qty din move s-ar putea să fie redundant sau să includă aceste linii.
            # În Odoo 17, stock.move.product_uom_qty este cererea totală.
            # Când facem action_assign, se creează move_lines.
            # Dacă folosim și move și move_line, riscăm dubla numărare dacă move.location_dest_id este aceeași cu move_line.location_dest_id.

            # Strategie mai bună:
            # - Mișcările (moves) care au destinația într-o locație frunză sunt luate în calcul prin move.product_uom_qty.
            # - Move line-urile care au destinația într-o locație frunză (și al căror move are destinația în altă parte, ex: părinte)
            #   trebuie adunate, iar din move-ul părinte trebuie scăzut ce a fost deja distribuit în frunze.

            # Dar metoda read_group pe move deja filtrează după location_dest_id.
            # Dacă move are dest_id = PARENT, el nu apare în planned_sums pentru LEAVES.
            # Dacă move are dest_id = LEAF1, el apare în planned_sums pentru LEAF1.

            # Deci trebuie să adăugăm move_lines care au dest_id = LEAF1 dar move.dest_id != LEAF1
            ml_sums = MoveLine.read_group(
                [
                    ("location_dest_id", "in", leaves.ids),
                    ("state", "not in", ["done", "cancel"]),
                    ("move_id.location_dest_id", "not in", leaves.ids),  # Evităm dubla numărare
                ],
                ["quantity:sum"],
                ["location_dest_id"],
                lazy=False,
            )
            for rec in ml_sums:
                loc_id = rec["location_dest_id"][0]
                planned_qty_by_loc[loc_id] = planned_qty_by_loc.get(loc_id, 0.0) + rec.get("quantity", 0.0)

        for leaf in leaves:
            leaf.planned_products = float(planned_qty_by_loc.get(leaf.id, 0.0))

        if parents:
            for loc in parents.sorted(key=lambda l: len((l.parent_path or "").split("/")), reverse=True):
                loc.planned_products = sum(child.planned_products for child in loc.child_ids)

    def _compute_warehouse_occupancy(self):
        """Optimized compute using batched read_group and bottom-up aggregation.

        - For leaf locations: perform a single read_group over all leaves in the batch
          to fetch current quantities from stock.quant (quantity > 0)
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

        exclude_location = self.env.context.get("exclude_location", self.env["stock.location"])
        if self in exclude_location:
            return False

        if not can_be_used:
            return False

        if self.max_products_leaf:
            # Capacitate pe frunză: nu depășim max_products_leaf
            # Luăm în calcul atât stocul actual cât și cel planificat
            planned_qty = self.planned_products

            # Adăugăm cantitatea din context (putaway_additional_qty) dacă există
            context_additional_qty = self.env.context.get("putaway_additional_qty")
            if context_additional_qty is None:
                context_additional_qty = self.env.context.get("additional_qty")

            if isinstance(context_additional_qty, dict):
                planned_qty += context_additional_qty.get(self.id, 0.0)
            elif isinstance(context_additional_qty, int | float):
                planned_qty += context_additional_qty

            if (self.current_products + planned_qty) >= self.max_products_leaf:
                return False

        return True

    def _get_putaway_strategy(self, product, quantity=0, package=None, packaging=None, additional_qty=None):
        putaway_location = super()._get_putaway_strategy(product, quantity, package, packaging, additional_qty)
        if self.env.context.get("putaway_location_standard"):
            return putaway_location

        # Dacă am găsit o locație

        if putaway_location.child_ids:
            quants = self.env["stock.quant"].search(
                [
                    ("product_id", "=", product.id),
                    ("location_id", "child_of", putaway_location.id),
                    ("location_id.usage", "=", "internal"),
                    ("quantity", ">", 0),
                ]
            )

            for quant in quants.sorted(key=lambda q: q.location_id.complete_name):
                candidate = quant.location_id
                # Transmitem contextul pentru a vedea ocuparea temporară
                if candidate._check_can_be_used(product, quantity, package):
                    return candidate

            leaf_locations = self.env["stock.location"].search(
                [
                    ("id", "child_of", putaway_location.id),
                    ("child_ids", "=", False),  # Esențial: găsește doar capătul ierarhiei
                    ("usage", "=", "internal"),
                    ("id", "!=", putaway_location.id),  # Excludem nodul curent
                ],
                order="complete_name asc",
            )

            for leaf in leaf_locations:
                # Transmitem contextul pentru a vedea ocuparea temporară
                if leaf._check_can_be_used(product, quantity, package):
                    return leaf
            # Daca nici o locatie nu e disponibila (toate pline), returnam originalul putaway_location
            # sau prima frunza daca vrem sa fortam macar o locatie interna.
            # Pentru a respecta ideea de "plin", returnam putaway_location si lasam splitarea sa se ocupe
            # sau super() sa decida.
        return putaway_location
