# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round


class ProductWarehouseLocation(models.Model):
    _name = "product.warehouse.location"
    _description = "Product Warehouse Location"

    product_id = fields.Many2one("product.template", index=True)
    warehouse_id = fields.Many2one("stock.warehouse", index=True)
    loc_rack = fields.Char("Rack Name", size=16)
    loc_row = fields.Char("Row Name", size=16)
    loc_shelf = fields.Char("Shelf Name", size=16)
    loc_case = fields.Char("Case Name", size=16)

    _product_product_uniq = models.Constraint(
        "unique(product_id, warehouse_id)",
        "Warehouse must be unique per product!",
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    loc_rack = fields.Char("Rack", size=16, compute="_compute_loc", inverse="_inverse_loc")
    loc_row = fields.Char("Row", size=16, compute="_compute_loc", inverse="_inverse_loc")
    loc_shelf = fields.Char("Shelf", size=16, compute="_compute_loc", inverse="_inverse_loc")
    loc_case = fields.Char("Case", size=16, compute="_compute_loc", inverse="_inverse_loc")

    warehouse_loc_ids = fields.One2many("product.warehouse.location", "product_id")
    is_inventory_ok = fields.Boolean("Inventory OK", tracking=True)  # nu are senes daca sunt mai multe locatii
    warehouse_stock = fields.Text(string="Stock/WH", compute="_compute_warehouse_stocks")

    def _get_detailed_warehouse_stocks(self, warehouses):
        """Batched stock details for warehouses displayed in 'detailed' mode.

        Returns {warehouse_id: {product_tmpl_id: {"total", "reserved", "restricted",
        "transit", "expected"}}}.
        Reserved quantities are counted only from non restricted locations, so
        restricted stock is not subtracted twice from the free stock.
        Transit quantities are pending incoming moves from other warehouses or
        transit locations; a chained transit leg is counted only once its origin
        moves are done, so goods that still wait upstream (e.g. on a supplier
        receipt) do not show as in transit.
        Expected quantities are pending receipts coming from suppliers,
        including receipt legs routed through a transit location.
        """
        result = {}
        variants = self.mapped("product_variant_ids")
        if not variants:
            return result
        empty_data = {"total": 0.0, "reserved": 0.0, "restricted": 0.0, "transit": 0.0, "expected": 0.0}
        restricted_locations = self.env["stock.location"].search(
            [("restricted_stock", "=", True), ("usage", "=", "internal")]
        )
        for warehouse in warehouses:
            wh_data = result[warehouse.id] = {}
            base_domain = [
                ("product_id", "in", variants.ids),
                ("location_id", "child_of", warehouse.view_location_id.id),
                ("location_id.usage", "=", "internal"),
            ]
            groups = self.env["stock.quant"]._read_group(
                base_domain, ["product_id"], ["quantity:sum", "reserved_quantity:sum"]
            )
            for product, quantity, reserved in groups:
                data = wh_data.setdefault(product.product_tmpl_id.id, dict(empty_data))
                data["total"] += quantity
                data["reserved"] += reserved
            if restricted_locations:
                groups = self.env["stock.quant"]._read_group(
                    base_domain + [("location_id", "child_of", restricted_locations.ids)],
                    ["product_id"],
                    ["quantity:sum", "reserved_quantity:sum"],
                )
                for product, quantity, reserved in groups:
                    data = wh_data.setdefault(product.product_tmpl_id.id, dict(empty_data))
                    data["restricted"] += quantity
                    data["reserved"] -= reserved
            pending_in_domain = [
                ("product_id", "in", variants.ids),
                ("state", "in", ("waiting", "confirmed", "partially_available", "assigned")),
                ("location_dest_id", "child_of", warehouse.view_location_id.id),
                ("location_dest_id.usage", "=", "internal"),
            ]
            groups = self.env["stock.move"]._read_group(
                pending_in_domain
                + [
                    ("location_id.usage", "in", ("internal", "transit")),
                    "!",
                    ("location_id", "child_of", warehouse.view_location_id.id),
                    # legs of a receipt routed through transit count as expected, not transit
                    "!",
                    ("move_orig_ids.location_id.usage", "=", "supplier"),
                    # a chained transit leg counts only once the goods physically
                    # reached the transit location (all origin moves done)
                    "|",
                    ("location_id.usage", "=", "internal"),
                    "!",
                    ("move_orig_ids.state", "!=", "done"),
                ],
                ["product_id"],
                ["product_qty:sum"],
            )
            for product, quantity in groups:
                data = wh_data.setdefault(product.product_tmpl_id.id, dict(empty_data))
                data["transit"] += quantity
            groups = self.env["stock.move"]._read_group(
                pending_in_domain
                + [
                    "|",
                    ("location_id.usage", "=", "supplier"),
                    "&",
                    ("location_id.usage", "=", "transit"),
                    ("move_orig_ids.location_id.usage", "=", "supplier"),
                ],
                ["product_id"],
                ["product_qty:sum"],
            )
            for product, quantity in groups:
                data = wh_data.setdefault(product.product_tmpl_id.id, dict(empty_data))
                data["expected"] += quantity
        return result

    def _compute_warehouse_stocks(self):
        display_free_quantity = self.env.context.get("display_free_quantity", False)
        # Consider only warehouses belonging to the current company to avoid multi-company leakage
        warehouses = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], order="name")
        if len(warehouses) == 1:
            # With a single warehouse in the current company, do not display the breakdown
            self.warehouse_stock = False
            return

        detailed_warehouses = warehouses.filtered(
            lambda warehouse: warehouse.kanban_display_stock == "detailed"
            and warehouse.lot_stock_id.usage == "internal"
        )
        detailed_stocks = self._get_detailed_warehouse_stocks(detailed_warehouses)

        for product in self:
            warehouse_stock_lines = []
            free_stock = 0.0
            has_detailed_lines = False
            rounding = product.uom_id.rounding
            for warehouse in warehouses:
                if warehouse.lot_stock_id.usage == "internal":
                    if warehouse.kanban_display_stock == "detailed":
                        data = detailed_stocks.get(warehouse.id, {}).get(product.id)
                        if not data:
                            continue
                        total = float_round(data["total"], precision_rounding=rounding)
                        reserved = float_round(data["reserved"], precision_rounding=rounding)
                        restricted = float_round(data["restricted"], precision_rounding=rounding)
                        transit = float_round(data["transit"], precision_rounding=rounding)
                        expected = float_round(data["expected"], precision_rounding=rounding)
                        free_stock += total - reserved - restricted
                        if total or reserved or restricted or transit or expected:
                            # R = reserved, B = blocked (restricted locations),
                            # T = in transit, E = expected from supplier
                            details = []
                            if reserved:
                                details.append(f"R: {reserved}")
                            if restricted:
                                details.append(f"B: {restricted}")
                            if transit:
                                details.append(f"T: {transit}")
                            if expected:
                                details.append(f"E: {expected}")
                            line = f"{warehouse.code}: {total}"
                            if details:
                                line += " (" + ", ".join(details) + ")"
                            warehouse_stock_lines.append(line)
                            has_detailed_lines = True
                        continue
                    if warehouse.kanban_display_stock == "main":
                        qty = self.with_context(location=warehouse.lot_stock_id.id)._compute_quantities_dict()
                    else:
                        qty = product.with_context(warehouse_id=warehouse.id)._compute_quantities_dict()
                    if display_free_quantity:
                        quantity_in_warehouse = qty[product.id]["qty_available"] - qty[product.id]["outgoing_qty"]
                        if quantity_in_warehouse:
                            line = f"{warehouse.code}: {quantity_in_warehouse}"
                            warehouse_stock_lines.append(line)
                    else:
                        quantity_in_warehouse = qty[product.id]["qty_available"]
                        if quantity_in_warehouse:
                            line = f"{warehouse.code}: {quantity_in_warehouse}"
                            warehouse_stock_lines.append(line)
            if has_detailed_lines:
                free_stock = float_round(free_stock, precision_rounding=rounding)
                warehouse_stock_lines.append(self.env._("FREE STOCK") + f": {free_stock}")
            product.warehouse_stock = "\n".join(warehouse_stock_lines)

    @api.depends_context("warehouse", "location")
    def _compute_loc(self):
        warehouse_id = self.env.context.get("warehouse", False)
        location_id = self.env.context.get("location", False)
        if not warehouse_id and location_id:
            if isinstance(location_id, int):
                # location = self.env["stock.location"].browse(location_id)
                # warehouse_id = location.warehouse_id.id
                warehouse = self.env["stock.warehouse"].search([("lot_stock_id", "=", location_id)], limit=1)
                if warehouse:
                    warehouse_id = warehouse.id
        if not warehouse_id:
            warehouse_id = self.env.ref("stock.warehouse0").id

        for product in self:
            domain = [
                ("product_id", "=", product.id),
                ("warehouse_id", "=", warehouse_id),
            ]
            loc = self.env["product.warehouse.location"].sudo().search(domain, limit=1)
            product.loc_rack = loc.loc_rack
            product.loc_row = loc.loc_row
            product.loc_shelf = loc.loc_shelf
            product.loc_case = loc.loc_case

    def _inverse_loc(self):
        warehouse_id = self.env.context.get("warehouse", False)
        if warehouse_id:
            for product in self:
                domain = [
                    ("product_id", "=", product.id),
                    ("warehouse_id", "=", warehouse_id),
                ]
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

    # def write(self, vals):
    #     res = super().write(vals)
    #     if "is_inventory_ok" in vals:
    #         self.with_context(active_test=False).mapped("product_variant_ids").write(
    #             {"is_inventory_ok": vals.get("is_inventory_ok")}
    #         )
    #     return res

    def variants_is_ok(self):
        self.ensure_one()
        is_inventory_ok = True
        for product in self.product_variant_ids:
            if not product.is_inventory_ok:
                is_inventory_ok = False
        return is_inventory_ok

    def get_location(self):
        """
        Get the location (first location from product, other are ignored)
        :return: stock location if found, else False
        """
        self.ensure_one()
        if self.warehouse_loc_ids:
            warehouse_loc = self.warehouse_loc_ids[0]
            if warehouse_loc.loc_row and warehouse_loc.loc_rack:
                if "/" in warehouse_loc.loc_row:
                    # multiple locations pe warehouse
                    rows = warehouse_loc.loc_row.split("/")
                    racks = warehouse_loc.loc_rack.split("/")
                    rack = racks[0]
                    row = rows[0]
                else:
                    rack = warehouse_loc.loc_rack
                    row = warehouse_loc.loc_row

                # search for location
                location_dest = (
                    warehouse_loc.warehouse_id.code
                    + "/"
                    + warehouse_loc.warehouse_id.lot_stock_id.name
                    + "/"
                    + row
                    + "/"
                    + rack
                )
                locations = self.env["stock.location"].search([("complete_name", "=", location_dest)])
                if not locations:
                    # try without leading zeros
                    if rack[0] == "0":
                        rack = rack[1:]
                        location_dest = (
                            warehouse_loc.warehouse_id.code
                            + "/"
                            + warehouse_loc.warehouse_id.lot_stock_id.name
                            + "/"
                            + row
                            + "/"
                            + rack
                        )
                        locations = self.env["stock.location"].search([("complete_name", "=", location_dest)])
                if not locations:
                    return False
                else:
                    return locations[0]
            else:
                return False
        else:
            return False

    def create_putaway_rule(self):
        """
        Create a putaway rule, if it doesn't exist
        :return: None
        """
        vals = []
        for product in self:
            location_dest = product.get_location()
            if location_dest:
                location_source = location_dest.warehouse_id.lot_stock_id
                for product_variant in product.product_variant_ids:
                    if not product_variant.putaway_rule_ids.filtered(
                        lambda loc_in: loc_in.location_in_id == location_source
                    ):
                        value = {
                            "company_id": product.company_id.id or self.env.user.company_id.id,
                            "product_id": product_variant.id,
                            "location_in_id": location_source.id,
                            "location_out_id": location_dest.id,
                        }
                        vals.append(value)
            # else:
            #     raise UserError(
            #         self.env._(f"No location can be fount for product {product.name}. Check product stock configuration")
            #     )
        if vals:
            self.env["stock.putaway.rule"].create(vals)

    def move_to_putaway_location(self):
        """
        Creates a picking to move all product variants in location found in variant's putaway rules
        No tracking (lots or serials) is used
        :return: created picking
        """
        self.ensure_one()
        location_id = False
        location_dest_id = False
        values = []
        for product in self.product_variant_ids:
            if product.putaway_rule_ids:
                rule_id = product.putaway_rule_ids[0]
                location_id = rule_id.location_in_id
                location_dest_id = rule_id.location_out_id
                quants = self.env["stock.quant"]._gather(product, location_id)
                qty = sum(quants.mapped("quantity"))
                value = {
                    "company_id": (self.company_id.id or self.env.user.company_id.id),
                    "date": fields.Datetime.now(),
                    "product_id": product.id,
                    "location_id": location_id.id,
                    "location_dest_id": location_dest_id.id,
                    "product_uom": product.uom_id.id,
                    "product_uom_qty": qty,
                    "picked": True,
                }
                values.append(value)
            else:
                raise UserError(self.env._("No putaway rule found for %s", product.name))
        if values:
            picking_type = self.env.ref("stock.picking_type_internal")
            picking_values = {
                "picking_type_id": picking_type.id,
                "location_id": location_id.id,
                "location_dest_id": location_dest_id.id,
                "move_ids": [(0, 0, line_vals) for line_vals in values],
            }
            picking = self.env["stock.picking"].create(picking_values)
            picking.action_confirm()
            for move in picking.move_ids:
                move._set_quantity_done(move.product_uom_qty)

            picking.move_ids.picked = True
            picking._action_done()
            return picking


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_inventory_ok = fields.Boolean("Inventory OK")

    @api.model
    def get_theoretical_quantity(
        self,
        product_id,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        to_uom=None,
    ):
        product_id = self.env["product.product"].browse(product_id)
        product_id.check_access("read")

        location_id = self.env["stock.location"].browse(location_id)
        lot_id = self.env["stock.lot"].browse(lot_id)
        package_id = self.env["stock.package"].browse(package_id)
        owner_id = self.env["res.partner"].browse(owner_id)
        to_uom = self.env["uom.uom"].browse(to_uom)
        quants = self.env["stock.quant"]._gather(
            product_id,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=True,
        )
        if lot_id:
            quants = quants.filtered(lambda q: q.lot_id == lot_id)
        theoretical_quantity = sum(quant.quantity for quant in quants)
        if to_uom and product_id.uom_id != to_uom:
            theoretical_quantity = product_id.uom_id._compute_quantity(theoretical_quantity, to_uom)
        return theoretical_quantity
