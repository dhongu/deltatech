# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    def post_inventory(self):
        super(StockInventory, self).post_inventory()
        for inventory in self:
            inventory.move_ids.write({"date": inventory.accounting_date or inventory.date})


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        values = super(InventoryLine, self)._get_move_values(qty, location_id, location_dest_id, out)
        values["date"] = self.inventory_id.accounting_date or self.inventory_id.date
        return values


class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, vals):
        date_fields = {"date", "date_expected"}
        use_date = self.env.context.get("force_period_date", False)
        if date_fields.intersection(vals):
            if not use_date:
                for move in self:
                    today = fields.Date.today()
                    if "date" in vals:
                        if move.date_expected.date() < today and move.date_expected < vals["date"]:
                            vals["date"] = move.date_expected
                        if move.date.date() < today and move.date.date() < vals["date"]:
                            vals["date"] = move.date
                        move.move_line_ids.write({"date": vals["date"]})
            else:
                if "date" in vals:
                    vals["date"] = use_date

        return super(StockMove, self).write(vals)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        return super(StockPicking, self.with_context(force_period_date=self.scheduled_date)).button_validate()

    def action_done(self):
        super(StockPicking, self).action_done()
        use_date = self.env.context.get("force_period_date", False)
        if use_date:
            self.write({"date": use_date, "date_done": use_date})
            self.move_lines.write({"date": use_date})  # 'date_expected': use_date,
            self.move_line_ids.write({"date": use_date})
