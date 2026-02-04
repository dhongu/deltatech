from odoo import fields, models
from odoo.tools.convert import safe_eval


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
        """Calculează cantitatea planificată prin agregarea liniilor de mișcare de stoc (stock.move.line).
        Sunt luate în calcul doar liniile care nu sunt în stările 'done' (finalizat) sau 'cancel' (anulat).
        """
        if not self:
            return
        MoveLine = self.env["stock.move.line"].sudo()
        leaves = self.filtered(lambda l: l.max_products_leaf)
        rest = self - leaves

        planned_qty_by_loc = {}
        if leaves:
            # Deci trebuie să adăugăm move_lines care au dest_id = LEAF1 dar move.dest_id != LEAF1
            domain = [
                ("location_dest_id", "in", leaves.ids),
                ("state", "not in", ["done", "cancel"]),
            ]
            exclude_move_line_id = self.env.context.get("exclude_move_line_id")
            if exclude_move_line_id:
                domain.append(("id", "!=", exclude_move_line_id))

            ml_sums = MoveLine.read_group(
                domain,
                ["quantity:sum"],
                ["location_dest_id"],
                lazy=False,
            )
            for rec in ml_sums:
                loc_id = rec["location_dest_id"][0]
                planned_qty_by_loc[loc_id] = rec.get("quantity", 0.0)

        # Alocăm rezultatele pentru locațiile frunză
        for leaf in leaves:
            leaf.planned_products = float(planned_qty_by_loc.get(leaf.id, 0.0))

        rest.planned_products = 0.0

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
        """Extinde verificarea standard a locației pentru a include limitările de capacitate definite pe frunze.
        Verifică atât stocul fizic actual cât și pe cel planificat (incoming).
        """
        can_be_used = super()._check_can_be_used(product, quantity, package, location_qty)
        if self.env.context.get("putaway_location_standard"):
            return can_be_used

        # Excludem locațiile marcate în context (de exemplu, cele care s-au umplut în timpul aceleiași operațiuni)
        exclude_location = self.env.context.get("exclude_location", self.env["stock.location"])
        if self in exclude_location:
            return False

        if not can_be_used:
            return False

        if self.max_products_leaf:
            # Verificăm dacă locația este deja plină la nivel de stoc fizic
            if self.current_products >= self.max_products_leaf:
                return False
            # Capacitate pe frunză: nu depășim max_products_leaf
            # Luăm în calcul atât stocul actual cât și cel planificat
            self._compute_planned_products()
            planned_qty = self.planned_products

            if (self.current_products + planned_qty) >= self.max_products_leaf:
                return False

        return True

    def _get_putaway_strategy(self, product, quantity=0, package=None, packaging=None, additional_qty=None):
        """Suprascrie strategia de putaway pentru a căuta automat sub-locații disponibile
        dacă locația de destinație configurată este plină sau are copii.
        """
        putaway_location = super()._get_putaway_strategy(product, quantity, package, packaging, additional_qty)
        if self.env.context.get("putaway_location_standard"):
            return putaway_location

        # Dacă am găsit o locație
        # de adauga un paramentru de sistem pentru a cauta o sublocatie
        get_param = self.env["ir.config_parameter"].sudo().get_param
        search_sublocation = get_param("deltatech_putaway_strategy.search_sublocation", "False")

        search_sublocation = safe_eval(search_sublocation)

        if search_sublocation and putaway_location.child_ids:
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

            # Dacă nu am găsit o locație cu același produs, căutăm orice locație frunză disponibilă
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

        return putaway_location
