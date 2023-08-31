# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BusinessIssue(models.Model):
    _name = "business.issue"
    _description = "Business Issue"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Name",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    code = fields.Char(
        string="Code",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    description = fields.Text(
        string="Description",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    area_id = fields.Many2one(
        string="Business area",
        comodel_name="business.area",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    raise_by_id = fields.Many2one(
        string="Raise by",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.user.partner_id.id,
    )
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
        required=True,
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
        required=True,
    )

    project_id = fields.Many2one(
        string="Project",
        comodel_name="business.project",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    process_id = fields.Many2one(
        string="Process",
        comodel_name="business.process",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    step_test_id = fields.Many2one(
        string="Step Test",
        comodel_name="business.process.step.test",
        readonly=True,
        domain=[("process_test_id.state", "!=", "done")],
        states={"draft": [("readonly", False)]},
    )

    open_date = fields.Date(
        string="Open Date",
        required=True,
        default=fields.Date.today,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    date_estimated = fields.Date(
        string="Estimated Date",
        readonly=True,
        states={"allocated": [("readonly", False)]},
    )
    solution = fields.Text(
        string="Solution",
        readonly=True,
        states={"allocated": [("readonly", False)]},
    )
    solution_date = fields.Date(
        string="Solution Date",
        readonly=True,
        states={"allocated": [("readonly", False)]},
    )

    closed_date = fields.Date(string="Closed Date", readonly=True, states={"in_test": [("readonly", False)]})
    closed_by_id = fields.Many2one(
        string="Closed by", comodel_name="res.partner", readonly=True, states={"in_test": [("readonly", False)]}
    )

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
        for issue in self:
            followers = self.env["res.partner"]
            if issue.raise_by_id not in issue.message_partner_ids:
                followers |= issue.raise_by_id
            if issue.responsible_id not in issue.message_partner_ids:
                followers |= issue.responsible_id
            if issue.customer_id not in issue.message_partner_ids:
                followers |= issue.customer_id
            issue.message_subscribe(followers.ids)

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
                if issue.step_test_id.process_test_id.state == "done":
                    raise UserError(_("This test is completed."))
                issue.process_id = issue.step_test_id.process_id
                issue.raise_by_id = issue.step_test_id.process_test_id.tester_id

    def button_send(self):
        self.write({"state": "open"})
        for issue in self:
            if issue.step_test_id:
                issue.step_test_id.write({"result": "failed"})

        self._add_followers()
        # trimite email la responsible

    def button_in_progress(self):
        self.write({"state": "allocated"})
        self._add_followers()

    def button_solved(self):
        for issue in self:
            if not issue.solution_date:
                raise UserError(_("The field Solution Date is required, please complete it to change status to Solved"))
            if not issue.solution:
                raise UserError(_("The field Solution is required, please complete it to change status to Solved"))
        self.write({"state": "solved"})

        self._add_followers()

    def button_in_test(self):
        self.write({"state": "in_test"})
        self._add_followers()

    def button_done(self):
        for issue in self:
            if not issue.closed_date:
                raise UserError(_("The field Closed Date is required, please complete it to change status to Closed"))
            if not issue.closed_by_id:
                issue.closed_by_id = self.env.user.partner_id

            # mai sunt alte issue deschise
            if issue.step_test_id:
                domain = [("id", "!=", issue), ("step_test_id", "=", issue.step_test_id.id), ("state", "!=", "closed")]
                other_open_issues = self.search(domain)
                if not other_open_issues:
                    issue.step_test_id.write({"result": "passed"})

        self.write({"state": "closed"})
        self._add_followers()

    def button_reopened(self):
        self.write({"state": "reopened"})
        self._add_followers()

    def button_draft(self):
        self.write({"state": "draft"})


class BusinessOpenIssue(models.Model):
    _name = "business.open.issue"
    _description = "Business Open Issue"
    _inherit = "business.issue"
