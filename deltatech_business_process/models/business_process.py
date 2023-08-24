# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, fields, models


class BusinessProcess(models.Model):
    _name = "business.process"
    _description = "Business process"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description")
    area_id = fields.Many2one(string="Area", comodel_name="business.area", required=True)
    process_group_id = fields.Many2one(
        string="Process Group", comodel_name="business.process.group", domain="[('area_id', '=', area_id)]"
    )

    step_ids = fields.One2many(string="Steps", comodel_name="business.process.step", inverse_name="process_id")
    responsible_id = fields.Many2one(string="Responsible", comodel_name="res.partner")
    customer_id = fields.Many2one(string="Customer Responsible", comodel_name="res.partner")
    state = fields.Selection(
        [("draft", "Draft"), ("design", "Design"), ("test", "Test"), ("ready", "Ready"), ("production", "Production")],
        string="State",
        default="draft",
        tracking=True,
    )
    approved_id = fields.Many2one(string="Approved by", comodel_name="res.partner")
    test_ids = fields.One2many(string="Tests", comodel_name="business.process.test", inverse_name="process_id")
    project_id = fields.Many2one(string="Project", comodel_name="business.project", required=True)

    count_steps = fields.Integer(string="Steps", compute="_compute_count_steps")
    count_tests = fields.Integer(string="Tests", compute="_compute_count_tests")

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs_count")

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [
            (process.id, "{}{}".format(process.code and "[%s] " % process.code or "", process.name)) for process in self
        ]

    def _compute_count_steps(self):
        for process in self:
            process.count_steps = len(process.step_ids)

    def _compute_count_tests(self):
        for process in self:
            process.count_tests = len(process.test_ids)

    def action_open_step(self):
        domain = [("process_id", "=", self.id)]
        context = {
            "default_process_id": self.id,
            "default_sequence": len(self.step_ids) + 10,
            "default_responsible_id": self.responsible_id.id,
        }
        return {
            "name": _("Process Steps"),
            "domain": domain,
            "res_model": "business.process.step",
            "type": "ir.actions.act_window",
            "views": [(False, "list"), (False, "form")],
            "view_mode": "tree,form",
            "context": context,
        }

    def action_open_test(self):
        domain = [("process_id", "=", self.id)]
        context = {
            "default_process_id": self.id,
        }
        return {
            "name": _("Process Tests"),
            "domain": domain,
            "res_model": "business.process.test",
            "type": "ir.actions.act_window",
            "views": [(False, "list"), (False, "form")],
            "view_mode": "tree,form",
            "context": context,
        }

    def get_attachment_domain(self):
        domain = [("res_model", "=", "business.process"), ("res_id", "=", self.id)]
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


class BusinessProcessStep(models.Model):
    _name = "business.process.step"
    _description = "Business process step"
    _order = "sequence"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description")
    process_id = fields.Many2one(string="Process", comodel_name="business.process", required=True)
    sequence = fields.Integer(string="Sequence", required=True, default=10)

    responsible_id = fields.Many2one(string="Responsible Step", comodel_name="res.partner")

    development_ids = fields.Many2many(
        string="Developments",
        comodel_name="business.development",
        relation="business_development_step_rel",
        column1="step_id",
        column2="development_id",
    )

    transaction_id = fields.Many2one(string="Transaction", comodel_name="business.transaction")
    transaction_type = fields.Selection(related="transaction_id.transaction_type")
    role_id = fields.Many2one(string="Role", comodel_name="business.role")

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [(step.id, "{}{}".format(step.code and "[%s] " % step.code or "", step.name)) for step in self]
