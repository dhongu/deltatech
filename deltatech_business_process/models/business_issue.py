# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessIssue(models.Model):
    _name = "business.issue"
    _description = "Business Issue"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", default=lambda self: self.env["ir.sequence"].next_by_code("business.issue"))
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

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [(item.id, "{}{}".format(item.code and "[%s] " % item.code or "", item.name)) for item in self]


class BusinessOpenIssue(models.Model):
    _name = "business.open.issue"
    _description = "Business Open Issue"
    _inherit = "business.issue"