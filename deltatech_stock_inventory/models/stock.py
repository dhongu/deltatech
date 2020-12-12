# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

# TODO: de adaugat pretul si in wizardul ce permite modificarea stocului


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    name = fields.Char(string="Name", default="/", copy=False)
    date = fields.Datetime(
        string="Inventory Date", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    note = fields.Text(string="Note")
    filterbyrack = fields.Char("Rack")

    def unlink(self):
        if any(inventory.state not in ("draft", "cancel") for inventory in self):
            raise UserError(_("You can only delete draft inventory."))
        return super(StockInventory, self).unlink()

    def _get_inventory_lines_values(self):
        lines = super(StockInventory, self)._get_inventory_lines_values()
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
            if inventory.name == "/":
                sequence = self.env.ref("deltatech_stock_inventory.sequence_inventory_doc")
                if sequence:
                    values["name"] = sequence.next_by_id()

            inventory.write(values)
            # for line in inventory.line_ids:
            #     line.write({'standard_price': line.get_price()})
        res = super(StockInventory, self).action_check()
        return res

    def action_done(self):
        super(StockInventory, self).action_done()
        for inv in self:
            for move in inv.move_ids:
                if move.date_expected != inv.date or move.date != inv.date:
                    move.write({"date_expected": inv.date, "date": inv.date})
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
    loc_rack = fields.Char("Rack", size=16, related="product_id.loc_rack", store=True)
    loc_row = fields.Char("Row", size=16, related="product_id.loc_row", store=True)
    loc_case = fields.Char("Case", size=16, related="product_id.loc_case", store=True)
    is_ok = fields.Boolean("Is Ok", default=True)

    @api.onchange("product_id", "location_id", "product_uom_id", "prod_lot_id", "partner_id", "package_id")
    def _onchange_quantity_context(self):
        res = super(StockInventoryLine, self)._onchange_quantity_context()
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
        for inventory_line in self:
            if inventory_line.product_id.cost_method == "fifo" and use_inventory_price:
                inventory_line.product_id.write(
                    {"standard_price": inventory_line.standard_price}
                )  # actualizare pret in produs
        moves = super(StockInventoryLine, self)._generate_moves()
        self.set_last_last_inventory()
        return moves

    def set_last_last_inventory(self):
        for inventory_line in self:
            prod_last_inventory_date = inventory_line.product_id.last_inventory_date
            product_tmpl_inventory_date = inventory_line.product_id.product_tmpl_id.last_inventory_date
            inventory_date = inventory_line.inventory_id.date.date()
            if not prod_last_inventory_date or prod_last_inventory_date < inventory_date:
                inventory_line.product_id.write(
                    {"last_inventory_date": inventory_date, "last_inventory_id": inventory_line.inventory_id.id}
                )
                if not product_tmpl_inventory_date or product_tmpl_inventory_date < inventory_date:
                    inventory_line.product_id.product_tmpl_id.write(
                        {"last_inventory_date": inventory_date, "last_inventory_id": inventory_line.inventory_id.id}
                    )

    @api.onchange("product_qty")
    def onchange_product_qty(self):
        self.is_ok = True
