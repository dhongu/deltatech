# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class BusinessProject(models.Model):
    _name = "business.project"
    _description = "Business project"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(string="Code")
    name = fields.Char(string="Name", required=True)
    customer_id = fields.Many2one(string="Customer", comodel_name="res.partner")
    logo = fields.Image()
    state = fields.Selection(
        [
            ("preparation", "Preparation"),
            ("exploration", "Exploration"),
            ("realization", "Realization"),
            ("deployment", "Deployment"),
            ("running", "Running"),
            ("closed", "Closed"),
        ],
        string="State",
        default="preparation",
    )
    date_start = fields.Date(string="Start date")
    date_go_live = fields.Date(string="Go live date")
    process_ids = fields.One2many(string="Processes", comodel_name="business.process", inverse_name="project_id")

    issue_ids = fields.One2many(string="Issues", comodel_name="business.issue", inverse_name="project_id")

    count_processes = fields.Integer(string="Count Processes", compute="_compute_count_processes")
    count_issues = fields.Integer(string="Count Issues", compute="_compute_count_issues")
    count_steps = fields.Integer(string="Steps", compute="_compute_count_steps")
    count_developments = fields.Integer(string="Developments", compute="_compute_count_developments")

    responsible_id = fields.Many2one(
        string="Responsible",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
    )
    team_member_ids = fields.Many2many(string="Team members", comodel_name="res.partner")
    total_project_duration = fields.Float(string="Total project duration")

    @api.model
    def create(self, vals):
        if not vals.get("code", False):
            vals["code"] = self.env["ir.sequence"].next_by_code(self._name)
        result = super().create(vals)
        return result

    def _compute_display_name(self):
        for project in self:
            project.display_name = "{}{}".format(project.code and f"[{project.code}] " or "", project.name)

    def _compute_count_processes(self):
        for project in self:
            project.count_processes = len(project.process_ids)

    def _compute_count_issues(self):
        for project in self:
            project.count_issues = len(project.issue_ids)

    def _compute_count_steps(self):
        for project in self:
            project.count_steps = sum(process.count_steps for process in project.process_ids)

    def _compute_count_developments(self):
        for project in self:
            developments = self.env["business.development"]
            for process in project.process_ids:
                developments |= process.development_ids
            project.count_developments = len(developments)

    def action_view_processes(self):
        domain = [("project_id", "=", self.id)]
        context = {
            "default_project_id": self.id,
            "default_customer_id": self.customer_id.id,
        }
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_process")
        action.update({"domain": domain, "context": context})
        return action

    def action_view_issue(self):
        domain = [("project_id", "=", self.id)]
        context = {
            "default_project_id": self.id,
            "default_customer_id": self.customer_id.id,
        }

        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_issue")
        action.update({"domain": domain, "context": context})
        return action

    def action_view_step(self):
        domain = [("process_id", "=", self.process_ids.ids)]
        context = {"default_project_id": self.id}
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_process_step")
        action.update({"domain": domain, "context": context})
        return action

    def action_view_developments(self):
        developments = self.env["business.development"]
        for process in self.process_ids:
            developments |= process.development_ids

        domain = [("id", "=", developments.ids)]
        context = {"default_project_id": self.id}
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_development")
        action.update({"domain": domain, "context": context})
        return action

    def calculate_total_project_duration(self):
        for project in self:
            project.total_project_duration = sum(process.duration_for_completion for process in project.process_ids)
