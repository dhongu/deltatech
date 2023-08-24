# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class BusinessProcessTest(models.Model):
    _name = "business.process.test"
    _description = "Business process Test"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    process_id = fields.Many2one(string="Process", comodel_name="business.process", required=True)
    tester_id = fields.Many2one(string="Tester", comodel_name="res.partner", required=True)
    date_start = fields.Date(string="Date start")
    date_end = fields.Date(string="Date end")
    state = fields.Selection(
        [("draft", "Draft"), ("run", "Run"), ("wait", "Waiting"), ("done", "Done")],
        string="State",
        tracking=True,
        default="draft",
    )
    scope = fields.Selection(
        [
            ("internal", "Internal"),
            ("integration", "Integration"),
            ("user_acceptance", "User Acceptance"),
            ("regression", "Regression"),
            ("other", "Other"),
        ],
        string="Scope",
        required=True,
        default="other",
    )

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs_count")

    test_step_ids = fields.One2many(
        string="Test steps", comodel_name="business.process.step.test", inverse_name="process_test_id"
    )

    def get_attachment_domain(self):
        domain = [("res_model", "=", self._name), ("res_id", "=", self.id)]
        return domain

    def _compute_attached_docs_count(self):
        for order in self:
            domain = order.get_attachment_domain()
            order.doc_count = self.env["ir.attachment"].search_count(domain)

    def attachment_tree_view(self):
        domain = self.get_attachment_domain()
        return {
            "name": _("Attachments"),
            "domain": domain,
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "kanban,tree,form",
            "context": "{{'default_res_model': '{}','default_res_id': {}}}".format(self._name, self.id),
        }

    @api.onchange("process_id")
    def _nchange_process_id(self):
        if self.process_id:
            self.test_step_ids = [(5, 0, 0)]
            for step in self.process_id.step_ids:
                self.test_step_ids = [(0, 0, {"step_id": step.id})]


class BusinessProcessStepTest(models.Model):
    _name = "business.process.step.test"
    _description = "Business Process Step Test"

    process_test_id = fields.Many2one(string="Process Test", comodel_name="business.process.test", required=True)
    step_id = fields.Many2one(string="Step", comodel_name="business.process.step", required=True)

    sequence = fields.Integer(string="Sequence", related="step_id.sequence", store=True)
    name = fields.Char(string="Name", related="step_id.name", store=True)
    description = fields.Text(string="Description", related="step_id.description", store=True)
    transaction_id = fields.Many2one(
        string="Transaction", comodel_name="business.transaction", related="step_id.transaction_id", store=True
    )
    responsible_id = fields.Many2one(string="Responsible", comodel_name="res.partner", store=True)

    result = fields.Selection(
        [
            ("draft", "Draft"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        string="Result",
    )
    data_used = fields.Text(string="Data used")
    data_result = fields.Text(string="Data result")

    date_start = fields.Date(string="Date start")
    date_end = fields.Date(string="Date end")
