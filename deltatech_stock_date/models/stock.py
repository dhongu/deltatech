# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


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
                        acc_date = fields.Date.to_date(vals["date"])
                        move_date = fields.Date.to_date(move.date)
                        if move_date < today and move_date < acc_date:
                            vals["date"] = move_date
                        move.move_line_ids.write({"date": vals["date"]})
            else:
                if "date" in vals:
                    vals["date"] = use_date

        return super().write(vals)

    def _action_done(self, cancel_backorder=False):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        restrict_date = safe_eval(get_param("restrict_stock_move_date_last_months", "False"))
        restrict_date_future = safe_eval(get_param("restrict_stock_move_date_future", "False"))
        if restrict_date:
            # se verifica daca data este in intervalul permis
            last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
            start_day_of_prev_month = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)
            if restrict_date_future:
                end_day_of_current_month = date.today()
            else:
                end_day_of_current_month = date.today().replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
            use_date = self.env.context.get("force_period_date", False)
            if use_date:
                if start_day_of_prev_month <= use_date.date() <= end_day_of_current_month:
                    pass
                else:
                    raise UserError(_("Cannot validate stock move due to date restriction."))
                self.check_lock_date(use_date)
            else:
                for move in self:
                    if start_day_of_prev_month <= move.date.date() <= end_day_of_current_month:
                        pass
                    else:
                        raise UserError(_("Cannot validate stock move due to date restriction."))
                    move.check_lock_date(move.date)
        return super()._action_done(cancel_backorder)

    def check_lock_date(self, move_date):
        lock_date = self.env.user.company_id._get_user_fiscal_lock_date()
        if move_date.date() < lock_date:
            raise UserError(_("Cannot validate stock move due to account date restriction."))


class StockPicking(models.Model):
    _inherit = "stock.picking"

    request_effective_date = fields.Boolean(related="picking_type_id.request_effective_date")
    forced_effective_date = fields.Datetime(
        string="Forced effective date",
        help="This date will override the effective date of the stock moves",
        copy=False,
    )

    @api.onchange("forced_effective_date")
    def _onchange_force_effective_date(self):
        if self.forced_effective_date:
            self.scheduled_date = self.forced_effective_date

    def action_toggle_is_locked(self):
        # se suprascrie metoda standard petnru a nu mai permite editarea
        return False

    def button_validate(self):
        to_check = False
        for picking in self:
            if picking.request_effective_date:
                to_check = True
        if to_check:
            if len(self) > 1:
                raise UserError(_("You cannot validate multiple pickings if stock_date module is installed"))
            else:
                if self.request_effective_date:
                    if self.forced_effective_date:
                        return super(
                            StockPicking, self.with_context(force_period_date=self.forced_effective_date)
                        ).button_validate()
                    else:
                        raise UserError(_("You must provide an effective date for the transfers."))
                else:
                    return super().button_validate()
        else:
            return super().button_validate()

    def _action_done(self):
        super()._action_done()
        use_date = self.env.context.get("force_period_date", False)
        if use_date:
            self.write({"date": use_date, "date_done": use_date})
            self.move_ids.write({"date": use_date})  # 'date_expected': use_date,
            self.move_line_ids.write({"date": use_date})


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    request_effective_date = fields.Boolean(
        string="Request effective date",
        help="If checked, a required effective date field will be added to the picking form."
        "All stock moves related to the picking will be forced to this date",
    )
