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
    tester_id = fields.Many2one(string="Tester", comodel_name="res.partner", domain="[('is_company', '=', False)]")
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
    count_steps = fields.Integer(string="Steps", compute="_compute_count_steps")
    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs_count")

    test_step_ids = fields.One2many(
        string="Test steps", comodel_name="business.process.step.test", inverse_name="process_test_id"
    )

    def _compute_count_steps(self):
        for test in self:
            test.count_steps = len(test.test_step_ids)

    def action_view_test_steps(self):
        domain = [("process_test_id", "=", self.id)]
        context = {"default_process_test_id": self.id}
        action = self.env["ir.actions.actions"]._for_xml_id(
            "deltatech_business_process.action_business_process_step_test"
        )
        action.update({"domain": domain, "context": context})
        return action

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
    def _onchange_process_id(self):
        if self.process_id:
            if not self.name:
                self.name = _("Testing %s") % self.process_id.name
            self.test_step_ids = [(5, 0, 0)]
            for step in self.process_id.step_ids:
                self.test_step_ids = [
                    (
                        0,
                        0,
                        {
                            "step_id": step.id,
                            "responsible_id": step.responsible_id.id,
                        },
                    )
                ]

    def action_run(self):
        self.ensure_one()
        self.write({"state": "run"})

        for test in self:
            date_start = min(test.test_step_ids.mapped("date_start")) or fields.Date.today()
            date_start = min(date_start, test.date_start or fields.Date.today())
            test_step_ids = test.test_step_ids.filtered(lambda x: not x.date_start)
            test_step_ids.write({"date_start": date_start})
            test.write({"date_start": date_start})
            if test.scope == "internal":
                test.process_id.write({"status_internal_test": "in_progress"})
            elif test.scope == "integration":
                test.process_id.write({"status_integration_test": "in_progress"})
            elif test.scope == "user_acceptance":
                test.process_id.write({"status_user_acceptance_test": "in_progress"})

    def action_wait(self):
        self.ensure_one()
        self.write({"state": "wait"})

    def action_done(self):
        self.ensure_one()
        self.write({"state": "done"})
        for test in self:
            date_end = max(test.test_step_ids.mapped("date_end")) or fields.Date.today()
            date_end = max(date_end, test.date_end or fields.Date.today())
            test_step_ids = test.test_step_ids.filtered(lambda x: not x.date_end)
            test_step_ids.write({"date_end": date_end})

            test_step_ids = test.test_step_ids.filtered(lambda x: not x.result == "draft")
            test_step_ids.write({"result": "passed"})
            test.write({"date_end": date_end})
            if test.scope == "internal":
                test.process_id.write({"status_internal_test": "done"})
            elif test.scope == "integration":
                test.process_id.write({"status_integration_test": "done"})
            elif test.scope == "user_acceptance":
                test.process_id.write({"status_user_acceptance_test": "done"})

    def action_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})
