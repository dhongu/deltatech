# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, fields, models


class BusinessProcess(models.Model):
    _name = "business.process"
    _description = "Business process"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True, tracking=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description")
    area_id = fields.Many2one(string="Area", comodel_name="business.area", required=True)
    process_group_id = fields.Many2one(
        string="Process Group", comodel_name="business.process.group", domain="[('area_id', '=', area_id)]"
    )

    step_ids = fields.One2many(
        string="Steps",
        comodel_name="business.process.step",
        inverse_name="process_id",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    responsible_id = fields.Many2one(string="Responsible", comodel_name="res.partner")
    customer_id = fields.Many2one(string="Customer Responsible", comodel_name="res.partner")
    state = fields.Selection(
        [("draft", "Draft"), ("design", "Design"), ("test", "Test"), ("ready", "Ready"), ("production", "Production")],
        string="State",
        default="draft",
        tracking=True,
    )

    test_ids = fields.One2many(string="Tests", comodel_name="business.process.test", inverse_name="process_id")
    project_id = fields.Many2one(
        string="Project",
        comodel_name="business.project",
        required=True,
        readoly=True,
        states={"draft": [("readonly", False)]},
    )

    count_steps = fields.Integer(string="Steps", compute="_compute_count_steps")
    count_tests = fields.Integer(string="Tests", compute="_compute_count_tests")

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs_count")

    date_start_bbp = fields.Date(
        string="Start BBP",
        help="Start date business blueprint",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    date_end_bbp = fields.Date(
        string="End BBP",
        help="End date business blueprint",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    completion_bbp = fields.Float(
        string="Completion",
        help="Completion business blueprint",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    approved_id = fields.Many2one(string="Approved by", comodel_name="res.partner")

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
