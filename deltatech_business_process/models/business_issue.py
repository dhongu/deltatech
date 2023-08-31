# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class BusinessIssue(models.Model):
    _name = "business.issue"
    _description = "Business Issue"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    description = fields.Text(string="Description")
    area_id = fields.Many2one(string="Business area", comodel_name="business.area")
    responsible_id = fields.Many2one(string="Responsible", comodel_name="res.partner")
    customer_id = fields.Many2one(string="Customer", comodel_name="res.partner")

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("allocated", "Allocated"),
            ("solved", "Solved"),
            ("in_test", "In Test Business"),
            ("reopened", "Reopened"),
            ("closed", "Closed"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # critical, major, minor, cosmetic
    severity = fields.Selection(
        [("critical", "Critical"), ("major", "Major"), ("minor", "Minor"), ("cosmetic", "Cosmetic")],
        string="Severity",
        default="minor",
    )

    # defect, open issue, improvement, change request, operation, other
    category = fields.Selection(
        [
            ("defect", "Defect"),
            ("open_issue", "Open Issue"),
            ("improvement", "Improvement"),
            ("change_request", "Change Request"),
            ("operation", "Operation"),
            ("other", "Other"),
        ],
        string="Category",
        default="defect",
    )

    project_id = fields.Many2one(string="Project", comodel_name="business.project", required=True)
    process_id = fields.Many2one(string="Process", comodel_name="business.process")
    step_test_id = fields.Many2one(string="Step Test", comodel_name="business.process.step.test")

    open_date = fields.Date(string="Open Date", required=True, default=fields.Date.today)

    date_estimated = fields.Date(string="Estimated Date")
    solution = fields.Text(string="Solution")
    solution_date = fields.Date(string="Solution Date")

    closed_date = fields.Date(string="Closed Date")
    closed_by_id = fields.Many2one(string="Closed by", comodel_name="res.partner")

    @api.model
    def create(self, vals):
        if not vals.get("code", False):
            vals["code"] = self.env["ir.sequence"].next_by_code(self._name)
        result = super().create(vals)
        return result

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [(item.id, "{}{}".format(item.code and "[%s] " % item.code or "", item.name)) for item in self]

    def _add_followers(self):
        for process in self:
            followers = self.env["res.partner"]
            if process.responsible_id not in process.message_partner_ids:
                followers |= process.responsible_id
            if process.customer_id not in process.message_partner_ids:
                followers |= process.customer_id
            process.message_subscribe(followers.ids)

    @api.onchange("process_id")
    def _onchange_process_id(self):
        for issue in self:
            if issue.process_id:
                issue.project_id = issue.process_id.project_id
                issue.customer_id = issue.process_id.customer_id
                issue.responsible_id = issue.process_id.responsible_id
                issue.area_id = issue.process_id.area_id

    @api.onchange("step_test_id")
    def _onchange_step_test_id(self):
        for issue in self:
            if issue.step_test_id:
                issue.process_id = issue.step_test_id.process_id

    def button_send(self):
        self.write({"state": "open"})
        # trimite email la responsible

    def button_in_progress(self):
        self.write({"state": "allocated"})

    def button_solved(self):
        self.write({"state": "solved"})

    def button_in_test(self):
        self.write({"state": "in_test"})

    def button_done(self):
        self.write({"state": "closed"})

    def button_draft(self):
        self.write({"state": "draft"})


class BusinessOpenIssue(models.Model):
    _name = "business.open.issue"
    _description = "Business Open Issue"
    _inherit = "business.issue"
