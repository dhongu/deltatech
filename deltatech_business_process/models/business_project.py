# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, fields, models


class BusinessProject(models.Model):
    _name = "business.project"
    _description = "Business project"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(string="Code")
    name = fields.Char(string="Name", required=True)
    customer_id = fields.Many2one(string="Customer Responsible", comodel_name="res.partner")

    state = fields.Selection(
        [
            ("preparation", "Preparation"),
            ("exploitation", "Exploitation"),
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
    count_processes = fields.Integer(string="Processes", compute="_compute_count_processes")

    team_member_ids = fields.Many2many(string="Team members", comodel_name="res.partner")

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [
            (project.id, "{}{}".format(project.code and "[%s] " % project.code or "", project.name)) for project in self
        ]

    def _compute_count_processes(self):
        for project in self:
            project.count_processes = len(project.process_ids)

    def action_open_processes(self):
        domain = [("project_id", "=", self.id)]
        context = {
            "default_project_id": self.id,
            "default_customer_id": self.customer_id.id,
        }
        return {
            "name": _("Project Processes"),
            "domain": domain,
            "res_model": "business.process",
            "type": "ir.actions.act_window",
            "views": [(False, "list"), (False, "form")],
            "view_mode": "tree,form",
            "context": context,
        }
