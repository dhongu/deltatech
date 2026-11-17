# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class KaizenProject(models.Model):
    _name = "kaizen.project"
    _description = "Kaizen Improvement Project"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(required=True, tracking=True)
    reference = fields.Char(readonly=True, copy=False, index=True, default="/")
    loss_type = fields.Selection(
        [
            ("scrap", "Scrap"),
            ("rework", "Rework"),
            ("downtime", "Downtime"),
            ("overtime", "Overtime"),
            ("material_waste", "Material waste"),
            ("other", "Other"),
        ],
        required=True,
        default="other",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("analysis", "Analysis"),
            ("actions", "Actions"),
            ("verification", "Verification"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    description = fields.Html()
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    date_start = fields.Date(required=True, default=fields.Date.context_today)
    date_deadline = fields.Date()
    date_closed = fields.Date(readonly=True, copy=False)

    baseline_date = fields.Date(string="Baseline Date")
    baseline_value = fields.Monetary(
        string="Baseline Loss / Month",
        currency_field="currency_id",
        default=0.0,
        tracking=True,
    )
    measured_date = fields.Date(string="Measured Date")
    current_value = fields.Monetary(
        string="Current Loss / Month",
        currency_field="currency_id",
        default=0.0,
        tracking=True,
    )
    target_value = fields.Monetary(
        string="Target Loss / Month",
        currency_field="currency_id",
        default=0.0,
    )
    savings_monthly = fields.Monetary(
        string="Monthly Savings",
        currency_field="currency_id",
        compute="_compute_savings",
    )
    savings_annual = fields.Monetary(
        string="Annual Savings (projection)",
        currency_field="currency_id",
        compute="_compute_savings",
        help="Monthly savings multiplied by 12. A projection, not a measured figure.",
    )
    is_target_reached = fields.Boolean(compute="_compute_is_target_reached")

    why_ids = fields.One2many("kaizen.why", "project_id", string="5 Why")
    ishikawa_ids = fields.One2many("kaizen.ishikawa.cause", "project_id", string="Ishikawa Causes")
    action_ids = fields.One2many("kaizen.action", "project_id", string="Actions")
    action_open_count = fields.Integer(compute="_compute_action_counts")
    action_count = fields.Integer(compute="_compute_action_counts")

    @api.depends("action_ids.state")
    def _compute_action_counts(self):
        for project in self:
            project.action_count = len(project.action_ids)
            project.action_open_count = len(project.action_ids.filtered(lambda a: a.state != "done"))

    @api.depends("baseline_value", "current_value")
    def _compute_savings(self):
        for project in self:
            project.savings_monthly = project.baseline_value - project.current_value
            project.savings_annual = project.savings_monthly * 12

    @api.depends("target_value", "current_value")
    def _compute_is_target_reached(self):
        for project in self:
            project.is_target_reached = bool(project.target_value > 0 and project.current_value <= project.target_value)

    @api.constrains("baseline_value", "current_value", "target_value")
    def _check_values_not_negative(self):
        for project in self:
            if project.baseline_value < 0 or project.current_value < 0 or project.target_value < 0:
                raise ValidationError(self.env._("Loss values cannot be negative."))

    @api.constrains("date_start", "date_deadline")
    def _check_dates(self):
        for project in self:
            if project.date_deadline and project.date_deadline < project.date_start:
                raise ValidationError(self.env._("The deadline cannot be before the start date."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("reference") or vals.get("reference") == "/":
                vals["reference"] = self.env["ir.sequence"].next_by_code("kaizen.project") or "/"
        return super().create(vals_list)

    def action_start_analysis(self):
        self.write({"state": "analysis"})

    def action_start_actions(self):
        self.write({"state": "actions"})

    def action_start_verification(self):
        for project in self:
            if project.action_open_count:
                raise UserError(
                    self.env._(
                        "%(count)s action(s) are still open. Finish them before verification.",
                        count=project.action_open_count,
                    )
                )
        self.write({"state": "verification"})

    def action_close(self):
        for project in self:
            if project.state in ("done", "cancelled"):
                raise UserError(self.env._("This project is already closed or cancelled."))
            if project.action_open_count:
                raise UserError(
                    self.env._(
                        "%(count)s action(s) are still open. Finish them before closing the project.",
                        count=project.action_open_count,
                    )
                )
            if not project.why_ids.filtered("is_root_cause"):
                raise UserError(self.env._("Mark a root cause in the 5 Why before closing the project."))
            if project.baseline_value <= 0:
                raise UserError(self.env._("The baseline loss must be positive before closing the project."))
        self.write({"state": "done", "date_closed": fields.Date.context_today(self)})

    def action_cancel(self):
        for project in self:
            if project.state == "done":
                raise UserError(self.env._("A closed project cannot be cancelled."))
        self.write({"state": "cancelled"})
