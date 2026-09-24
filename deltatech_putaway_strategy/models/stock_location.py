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
        self.env["stock.move"].sudo()
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

            ml_sums = MoveLine._read_group(
                domain,
                ["location_dest_id"],
                ["quantity:sum"],
            )
            for rec in ml_sums:
                loc_id = rec[0].id
                planned_qty_by_loc[loc_id] = rec[1]

        # Alocăm rezultatele pentru locațiile frunză
        for leaf in leaves:
            leaf.planned_products = float(planned_qty_by_loc.get(leaf.id, 0.0))

        rest.planned_products = 0.0

    def _compute_warehouse_occupancy(self):
        """Calcul optimizat al ocupării depozitului folosind batch read_group.
        - Pentru locații frunză: preia cantitățile actuale din stock.quant (unde qty > 0).
        - Pentru locații părinte: agregă valorile din copii în memorie.
        """
        Quant = self.env["stock.quant"].sudo()

        if not self:
            return

        leaves = self.filtered(lambda l: not l.child_ids)
        parents = self - leaves

        qty_by_loc = {}
        if leaves:
            sums = Quant._read_group(
                [("location_id", "in", leaves.ids), ("quantity", ">", 0)],
                ["location_id"],
                ["quantity:sum"],
            )
            qty_by_loc = {location.id: qty for location, qty in sums}

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

            # Verificăm capacitatea luând în calcul și marfa planificată să ajungă în această locație
            # Folosim valoarea calculată în batch (din cache-ul Odoo) pentru performanță
            planned_qty = self.planned_products

            if (self.current_products + planned_qty + quantity) > self.max_products_leaf:
                return False

        return True

    def _get_putaway_strategy(self, product, quantity=0, package=None, packaging=None, additional_qty=None):
        """Suprascrie strategia de putaway pentru a căuta automat sub-locații disponibile
        dacă locația de destinație configurată este plină sau are copii.
        """
        putaway_location = super()._get_putaway_strategy(product, quantity, package, packaging, additional_qty)
        if self.env.context.get("putaway_location_standard"):
            return putaway_location

        get_param = self.env["ir.config_parameter"].sudo().get_param

        prefer_existing = safe_eval(get_param("deltatech_putaway_strategy.prefer_existing_stock_location", "False"))
        if prefer_existing:
            existing_location = self._get_putaway_existing_stock_location(product, quantity, package, putaway_location)
            if existing_location:
                return existing_location

        # Dacă am găsit o locație
        # de adauga un paramentru de sistem pentru a cauta o sublocatie
        search_sublocation = get_param("deltatech_putaway_strategy.search_sublocation", "False")

        search_sublocation = safe_eval(search_sublocation)

        if search_sublocation and putaway_location.child_ids:
            # Încercăm mai întâi locațiile unde există deja același produs
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

    def _get_putaway_existing_stock_location(self, product, quantity, package, putaway_location):
        """Caută raftul pe care produsul are deja stoc, oriunde sub locația de intrare (`self`),
        chiar dacă nu e sub locația dată de regula de putaway.

        Acoperă produsele mutate fizic pe alt raft fără actualizarea regulii: regula trimite
        în continuare pe raftul vechi, iar căutarea din `search_sublocation` nu ajunge la raftul
        nou, pentru că se uită doar sub locația din regulă.

        Contează doar stocul liber (cantitate minus rezervat): un raft de pe care marfa tocmai
        pleacă nu e o destinație. Locațiile sursă ale operației, primite în contextul
        `putaway_exclude_location_ids`, sunt excluse explicit, ca un transfer de pe raft să nu
        primească drept destinație chiar raftul de pe care pleacă.

        Întoarce o locație goală dacă produsul e deja pe locația din regulă (nu e nimic de
        corectat) sau dacă niciun raft cu stoc nu mai are capacitate; atunci rămâne valabilă
        strategia obișnuită.
        """
        empty = self.env["stock.location"]
        if not product or not self.child_ids:
            return empty
        excluded_ids = [self.id, *self.env.context.get("putaway_exclude_location_ids", [])]
        groups = self.env["stock.quant"]._read_group(
            [
                ("product_id", "=", product.id),
                ("location_id", "child_of", self.id),
                ("location_id", "not in", excluded_ids),
                ("location_id.usage", "=", "internal"),
                ("location_id.child_ids", "=", False),
                ("quantity", ">", 0),
            ],
            ["location_id"],
            ["quantity:sum", "reserved_quantity:sum"],
        )
        stock_by_location = [
            (location, quantity - reserved)
            for location, quantity, reserved in groups
            if product.uom_id.compare(quantity - reserved, 0) > 0
        ]
        if not stock_by_location:
            return empty
        locations = self.env["stock.location"].concat(*(location for location, _qty in stock_by_location))
        if putaway_location in locations:
            return empty
        # Raftul cu cea mai mare cantitate întâi; la egalitate, ordinea alfabetică, ca rezultatul
        # să fie stabil de la o scanare la alta.
        for location, _qty in sorted(stock_by_location, key=lambda item: (-item[1], item[0].complete_name)):
            if location._check_can_be_used(product, quantity, package):
                return location
        return empty
