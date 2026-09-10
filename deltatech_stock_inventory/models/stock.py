# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    name = fields.Char(string="Name", copy=False)
    date = fields.Datetime(
        string="Inventory Date",
        required=True,
    )
    note = fields.Text(string="Note")
    filterbyrack = fields.Char("Rack")

    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    total_theoretical_value = fields.Monetary(
        string="Theoretical Value",
        compute="_compute_total_values",
        groups="stock.group_stock_manager",
        help="Value of the on hand quantities, at the unit cost snapshotted on the lines.",
    )
    total_counted_value = fields.Monetary(
        string="Counted Value",
        compute="_compute_total_values",
        groups="stock.group_stock_manager",
    )
    total_diff_value = fields.Monetary(
        string="Difference Value",
        compute="_compute_total_values",
        groups="stock.group_stock_manager",
        help="Estimated value of the inventory difference, before validation.",
    )
    total_posted_value = fields.Monetary(
        string="Posted Value",
        compute="_compute_total_values",
        groups="stock.group_stock_manager",
        help="Value actually posted by the inventory moves, filled in at validation.",
    )

    @api.depends(
        "line_ids.theoretical_value",
        "line_ids.counted_value",
        "line_ids.diff_value",
        "line_ids.posted_value",
    )
    def _compute_total_values(self):
        for inventory in self:
            lines = inventory.line_ids.sudo()
            inventory.total_theoretical_value = sum(lines.mapped("theoretical_value"))
            inventory.total_counted_value = sum(lines.mapped("counted_value"))
            inventory.total_diff_value = sum(lines.mapped("diff_value"))
            inventory.total_posted_value = sum(lines.mapped("posted_value"))

    def _get_inventory_lines_values(self):
        lines = super()._get_inventory_lines_values()
        for line in lines:
            product = self.env["product.product"].browse(line["product_id"])
            price = product.standard_price
            line["standard_price"] = price

        for line in lines:
            line["is_ok"] = False
        return lines

    def action_check(self):
        for inventory in self:
            date = inventory.date
            values = {"date": date}
            if inventory.name in ("/", self.env._("New")):
                sequence = self.env.ref("deltatech_stock_inventory.sequence_inventory_doc")
                if sequence:
                    values["name"] = sequence.next_by_id()

            inventory.write(values)
            # for line in inventory.line_ids:
            #     line.write({'standard_price': line.get_price()})
        res = super().action_check()
        return res

    def _action_done(self):
        super()._action_done()
        for inv in self:
            for move in inv.move_ids:
                if move.date != inv.date:
                    move.write({"date": inv.date})
            inv.line_ids._snapshot_posted_value()
        return True

    def action_remove_not_ok(self):
        for line in self.line_ids:
            if not line.is_ok:
                line.unlink()

    def action_new_for_not_ok(self):
        new_inv = self.copy({"line_ids": False, "state": "confirm"})
        for line in self.line_ids:
            if not line.is_ok:
                line.write({"inventory_id": new_inv.id})


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"
    _order = "inventory_id, location_id, categ_id, product_id, prod_lot_id"

    categ_id = fields.Many2one("product.category", string="Category", related="product_id.categ_id", store=True)
    standard_price = fields.Float(string="Price")

    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    unit_value = fields.Monetary(
        string="Unit Value",
        readonly=True,
        groups="stock.group_stock_manager",
        help="Unit valuation cost snapshotted when the line was generated: the stock value of the "
        "matching quants divided by their quantity, falling back to the product cost. "
        "Unlike Price, it is not edited by the operator, so the values below stay comparable.",
    )
    theoretical_value = fields.Monetary(
        string="Theoretical Value",
        compute="_compute_line_values",
        store=True,
        groups="stock.group_stock_manager",
    )
    counted_value = fields.Monetary(
        string="Counted Value",
        compute="_compute_line_values",
        store=True,
        groups="stock.group_stock_manager",
    )
    diff_value = fields.Monetary(
        string="Difference Value",
        compute="_compute_line_values",
        store=True,
        groups="stock.group_stock_manager",
        help="Estimated value of the difference, available before validation.",
    )
    posted_value = fields.Monetary(
        string="Posted Value",
        readonly=True,
        groups="stock.group_stock_manager",
        help="Value actually posted by the inventory move of this line, filled in at validation. "
        "It can differ from the estimate for FIFO products, where the outgoing move is valued "
        "on the consumed layers.",
    )

    loc_rack = fields.Char("Rack Name", size=16, compute="_compute_loc", store=True)
    loc_row = fields.Char("Row Name", size=16, compute="_compute_loc", store=True)
    loc_case = fields.Char("Case Name", size=16, compute="_compute_loc", store=True)
    is_ok = fields.Boolean("Is Ok", default=True)

    @api.depends("unit_value", "theoretical_qty", "product_qty")
    def _compute_line_values(self):
        for line in self:
            line.theoretical_value = line.unit_value * line.theoretical_qty
            line.counted_value = line.unit_value * line.product_qty
            line.diff_value = line.counted_value - line.theoretical_value

    def _get_unit_value(self):
        """Costul unitar de valorizare al liniei, citit din quanturi si cazut pe costul produsului."""
        self.ensure_one()
        quants = self.get_quants().sudo()
        # quant.value nu depinde de standard_price, deci ramane in cache dupa o schimbare
        # de cost in aceeasi tranzactie; la re-fotografiere vrem valoarea recalculata
        quants.invalidate_recordset(["value"])
        quantity = sum(quants.mapped("quantity"))
        value = sum(quants.mapped("value"))
        if quantity and value:
            return value / quantity
        company = self.company_id or self.env.company
        return self.product_id.with_company(company).sudo().standard_price

    def _snapshot_unit_value(self):
        # Scris cu sudo: unit_value e restrans la managerii de stoc, dar inventarul
        # e generat de operatori care nu au grupul.
        for line in self:
            line.sudo().unit_value = line._get_unit_value()

    def _snapshot_posted_value(self):
        for line in self:
            moves = line.inventory_id.move_ids.sudo().filtered(lambda move, ln=line: move.inventory_line_id == ln)
            if not moves:
                continue
            sign = -1 if line.difference_qty < 0 else 1
            line.sudo().posted_value = sign * sum(abs(value) for value in moves.mapped("value"))

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        values = super()._get_move_values(qty, location_id, location_dest_id, out)
        values["inventory_line_id"] = self.id
        return values

    def action_refresh_quantity(self):
        res = super().action_refresh_quantity()
        # Butonul reciteste stocul, deci si costul unitar de valorizare
        self.filtered(lambda line: line.state != "done")._snapshot_unit_value()
        return res

    @api.depends("location_id", "product_id")
    def _compute_loc(self):
        for line in self:
            warehouse = line.location_id.warehouse_id
            product = line.product_id.with_context(warehouse=warehouse.id)
            line.loc_rack = product.loc_rack
            line.loc_row = product.loc_row
            line.loc_case = product.loc_case

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if "standard_price" not in values:
                if "product_id" in values:
                    product = self.env["product.product"].browse(values["product_id"])
                    values["standard_price"] = product.standard_price
                elif self.env.context.get("default_product_id", False):
                    product = self.env["product.product"].browse(self.env.context.get("default_product_id", False))
                    values["standard_price"] = product.standard_price
        lines = super().create(vals_list)
        lines.filtered(lambda line: not line.sudo().unit_value)._snapshot_unit_value()
        return lines

    @api.onchange(
        "product_id",
        "location_id",
        "product_uom_id",
        "prod_lot_id",
        "partner_id",
        "package_id",
    )
    def _onchange_quantity_context(self):
        res = super()._onchange_quantity_context()
        self.standard_price = self.get_price()
        return res

    # todo: nu sunt sigur ca e bine ??? e posibil ca self sa fie gol

    @api.model
    def get_price(self):
        price = self.product_id.standard_price
        # if self.product_id.cost_method == 'fifo':
        #     if self.theoretical_qty:
        #         price = self.product_id.stock_value / self.theoretical_qty
        #         #price = self.product_id.with_context(to_date=self.accounting_date).stock_value / self.theoretical_qty
        return price

    def _generate_moves(self):
        config_parameter = self.env["ir.config_parameter"].sudo()
        use_inventory_price = config_parameter.get_param(key="stock.use_inventory_price", default="True")
        use_inventory_price = safe_eval(use_inventory_price)

        # actualizare pret in produs
        for inventory_line in self:
            if (
                not inventory_line.theoretical_qty
                or (
                    inventory_line.product_id.cost_method == "fifo"
                    or inventory_line.product_id.cost_method == "average"
                )
                and use_inventory_price
            ):
                inventory_line.product_id.sudo().with_context(disable_auto_svl=True).write(
                    {"standard_price": inventory_line.standard_price}
                )
        moves = super()._generate_moves()
        # self.set_last_last_inventory()
        return moves

    # def set_last_last_inventory(self):
    #     for inventory_line in self:
    #         prod_last_inventory_date = inventory_line.product_id.last_inventory_date
    #         product_tmpl_inventory_date = inventory_line.product_id.product_tmpl_id.last_inventory_date
    #         inventory_date = inventory_line.inventory_id.date.date()
    #         if not prod_last_inventory_date or prod_last_inventory_date < inventory_date:
    #             inventory_line.product_id.write(
    #                 {"last_inventory_date": inventory_date, "last_inventory_id": inventory_line.inventory_id.id}
    #             )
    #             if not product_tmpl_inventory_date or product_tmpl_inventory_date < inventory_date:
    #                 inventory_line.product_id.product_tmpl_id.write(
    #                     {"last_inventory_date": inventory_date, "last_inventory_id": inventory_line.inventory_id.id}
    #                 )

    @api.onchange("product_qty")
    def onchange_product_qty(self):
        self.is_ok = True
