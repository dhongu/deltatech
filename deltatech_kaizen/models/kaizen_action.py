# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
from odoo import api, fields, models


class KaizenAction(models.Model):
    _name = "kaizen.action"
    _description = "Kaizen Action"
    _order = "project_id, deadline, id"

    project_id = fields.Many2one("kaizen.project", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True)
    user_id = fields.Many2one("res.users", string="Responsible", required=True)
    deadline = fields.Date(required=True)
    state = fields.Selection(
        [("todo", "To Do"), ("done", "Done")],
        default="todo",
        required=True,
    )
    done_date = fields.Date(readonly=True, copy=False)
    is_overdue = fields.Boolean(compute="_compute_is_overdue")

    @api.depends("state", "deadline")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for action in self:
            action.is_overdue = bool(action.state != "done" and action.deadline and action.deadline < today)

    def action_done(self):
        today = fields.Date.context_today(self)
        for action in self:
            vals = {"state": "done"}
            if not action.done_date:
                vals["done_date"] = today
            action.write(vals)
