# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError

ACTIVITY_FIELDS = ("user_id", "deadline", "description")


class SafetyAction(models.Model):
    _name = "deltatech.safety.action"
    _description = "Safety Corrective Action"
    _order = "deadline, id"
    _check_company_auto = True

    event_id = fields.Many2one(
        "deltatech.safety.event", string="Safety event", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="event_id.company_id", store=True, index=True)
    description = fields.Char(required=True)
    user_id = fields.Many2one(
        "res.users", string="Responsible", required=True, default=lambda self: self.env.user, check_company=True
    )
    deadline = fields.Date(required=True, default=fields.Date.context_today)
    state = fields.Selection(
        selection=[("open", "Open"), ("done", "Done")],
        string="Status",
        required=True,
        readonly=True,
        default="open",
        copy=False,
    )
    done_date = fields.Date(readonly=True, copy=False)
    activity_id = fields.Many2one("mail.activity", readonly=True, copy=False, ondelete="set null")

    def _check_event_editable(self):
        if self.env.su or self.env.user.has_group("deltatech_safety_register.group_safety_manager"):
            return
        if self.event_id.filtered(lambda e: e.state == "closed"):
            raise UserError(self.env._("The safety event is closed; only a Safety manager can change its actions."))

    @api.model_create_multi
    def create(self, vals_list):
        actions = super().create(vals_list)
        actions._check_event_editable()
        for action in actions:
            action._schedule_activity()
        return actions

    def write(self, vals):
        if set(vals) - {"activity_id"}:
            self._check_event_editable()
        res = super().write(vals)
        if any(key in vals for key in ACTIVITY_FIELDS):
            for action in self.filtered(lambda a: a.state == "open"):
                action.activity_id.sudo().unlink()
                action._schedule_activity()
        return res

    def _schedule_activity(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        activity = self.event_id.activity_schedule(
            "mail.mail_activity_data_todo",
            date_deadline=max(self.deadline, today),
            summary=self.description,
            user_id=self.user_id.id,
        )
        self.activity_id = activity[:1]

    def action_done(self):
        self._check_event_editable()
        for action in self.filtered(lambda a: a.state == "open"):
            activity = action.activity_id
            action.write({"state": "done", "done_date": fields.Date.context_today(action), "activity_id": False})
            if activity.exists():
                activity.sudo().action_feedback(feedback=self.env._("Corrective action done."))
        return True
