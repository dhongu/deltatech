# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
from odoo import api, fields, models
from odoo.exceptions import ValidationError

MAX_WHY_LINES = 5


class KaizenWhy(models.Model):
    _name = "kaizen.why"
    _description = "Kaizen 5 Why Line"
    _order = "project_id, sequence, id"

    project_id = fields.Many2one("kaizen.project", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    name = fields.Text(string="Why? Because...", required=True)
    is_root_cause = fields.Boolean(string="Root Cause")

    @api.constrains("project_id", "is_root_cause")
    def _check_why_lines(self):
        for project in self.mapped("project_id"):
            if len(project.why_ids) > MAX_WHY_LINES:
                raise ValidationError(self.env._("A 5 Why analysis has at most %(max)s lines.", max=MAX_WHY_LINES))
            if len(project.why_ids.filtered("is_root_cause")) > 1:
                raise ValidationError(self.env._("Only one 5 Why line can be the root cause."))
