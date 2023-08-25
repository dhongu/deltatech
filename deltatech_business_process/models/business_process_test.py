# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class BusinessProcessTest(models.Model):
    _name = "business.process.test"
    _description = "Business process Test"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    process_id = fields.Many2one(string="Process", comodel_name="business.process", required=True)
    area_id = fields.Many2one(string="Area", comodel_name="business.area", related="process_id.area_id", store=True)
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
