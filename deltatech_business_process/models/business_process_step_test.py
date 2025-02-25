# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class BusinessProcessStepTest(models.Model):
    _name = "business.process.step.test"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Business Process Step Test"

    process_test_id = fields.Many2one(
        string="Process Test", comodel_name="business.process.test", required=True, ondelete="cascade"
    )
    state = fields.Selection(related="process_test_id.state", copy=False, store=True)
    step_id = fields.Many2one(string="Step", comodel_name="business.process.step", required=True)
    process_id = fields.Many2one(
        string="Process", comodel_name="business.process", related="step_id.process_id", store=True
    )
    test_started = fields.Boolean(string="Test started", default=False)
    sequence = fields.Integer(string="Sequence", related="step_id.sequence", store=True)
    name = fields.Char(string="Name", related="step_id.name", store=True)
    description = fields.Text(string="Description", related="step_id.description", store=True)
    transaction_id = fields.Many2one(
        string="Transaction", comodel_name="business.transaction", related="step_id.transaction_id", store=True
    )
    responsible_id = fields.Many2one(
        string="Responsible", comodel_name="res.partner", domain="[('is_company', '=', False)]", store=True
    )

    result = fields.Selection(
        [
            ("draft", "Draft"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        string="Result",
        default="draft",
        copy=False,
        index=True,
    )

    data_used = fields.Text(string="Data used")
    data_result = fields.Text(string="Data result")

    date_start = fields.Date(string="Date start", default=fields.Date.today)
    date_end = fields.Date(string="Date end")
    observation = fields.Text(string="Observation")

    feedback_by_id = fields.Many2one("res.partner", string="", domain="[('is_company', '=', False)]")
    feedback_text = fields.Text(string="Feedback")
    feedback_date = fields.Date(string="Feedback date")
    feedback_state = fields.Selection(
        [("draft", "Draft"), ("ok", "Ok"), ("not_ok", "Not ok")], string="Feedback state", default="draft"
    )
    count_issues = fields.Integer(string="Count Issues", compute="_compute_count_issues", store=True)

    issue_ids = fields.One2many("business.issue", "step_test_id", string="Issues")

    @api.depends("issue_ids")
    def _compute_count_issues(self):
        for record in self:
            record.count_issues = len(record.issue_ids.filtered(lambda x: x.state != "closed"))

    def action_view_issue(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_issue")
        domain = [("step_test_id", "=", self.id)]
        context = {
            "default_name": "Issue {}".format(self.name),
            "default_step_test_id": self.id,
            "default_project_id": self.process_id.project_id.id,
            "default_process_id": self.process_id.id,
            "default_responsible_id": self.responsible_id.id,
            "defulat_step_id": self.step_id.id,
            "default_area_id": self.process_id.area_id.id,
        }
        action.update({"domain": domain, "context": context})
        return action

    @api.onchange("result")
    def _onchange_result(self):
        if self.result == "passed":
            self.date_end = fields.Date.today()

    def reset_draft(self):
        self.write({"result": "draft", "date_end": False})

    def do_fail(self):
        self.write({"result": "failed", "date_end": fields.Date.today()})

    def do_pass(self):
        self.write({"result": "passed", "date_end": fields.Date.today()})
