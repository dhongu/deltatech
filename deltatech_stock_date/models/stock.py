# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _update_available_quantity(
        self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None
    ):
        res = super(StockQuant, self)._update_available_quantity(
            product_id, location_id, quantity, lot_id, package_id, owner_id, in_date
        )

        return res


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
                        date = fields.Date.to_date(vals["date"])
                        move_date = fields.Date.to_date(move.date)
                        if move_date < today and move_date < date:
                            vals["date"] = move_date
                        move.move_line_ids.write({"date": vals["date"]})
            else:
                if "date" in vals:
                    vals["date"] = use_date

        return super(StockMove, self).write(vals)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_toggle_is_locked(self):
        # se suprascrie metoda standard petnru a nu mai permite editarea
        return False

    def button_validate(self):
        return super(StockPicking, self.with_context(force_period_date=self.scheduled_date)).button_validate()

    def _action_done(self):
        super(StockPicking, self)._action_done()
        use_date = self.env.context.get("force_period_date", False)
        if use_date:
            self.write({"date": use_date, "date_done": use_date})
            self.move_lines.write({"date": use_date})  # 'date_expected': use_date,
            self.move_line_ids.write({"date": use_date})
