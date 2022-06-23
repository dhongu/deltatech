# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import safe_eval


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
                        val_date = fields.Date.to_date(vals["date"])
                        if move.date_expected.date() < today and move.date_expected.date() < val_date:
                            vals["date"] = move.date_expected
                        if move.date.date() < today and move.date.date() < val_date:
                            vals["date"] = move.date
                        move.move_line_ids.write({"date": vals["date"]})
            else:
                if "date" in vals:
                    vals["date"] = use_date

        return super(StockMove, self).write(vals)

    def _action_done(self, cancel_backorder=False):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        restrict_date = safe_eval(get_param("restrict_stock_move_date_last_months", "False"))
        if restrict_date:
            last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
            start_day_of_prev_month = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)
            end_day_of_current_month = date.today().replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
            for move in self:
                if start_day_of_prev_month < move.date.date() < end_day_of_current_month:
                    pass
                else:
                    raise UserError(_("Cannot validate stock move due to date restriction."))
        return super(StockMove, self)._action_done(cancel_backorder)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        if self.env.context.get("force_period_date", False):
            force_period_date = self.env.context["force_period_date"]
        else:
            transfer_at_scheduled_date = get_param("stock.transfer_at_scheduled_date", default="True")
            if safe_eval(transfer_at_scheduled_date):
                force_period_date = self.scheduled_date
            else:
                force_period_date = fields.Datetime.now()
        return super(StockPicking, self.with_context(force_period_date=force_period_date)).button_validate()

    def action_done(self):
        super(StockPicking, self).action_done()
        use_date = self.env.context.get("force_period_date", False)
        if use_date:
            self.write({"date": use_date, "date_done": use_date})
            self.move_lines.write({"date": use_date})  # 'date_expected': use_date,
            self.move_line_ids.write({"date": use_date})
